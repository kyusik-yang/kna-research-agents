#!/usr/bin/env python3
"""Seniority at an Assembly for KNA members: one tested source of truth.

    term_number(mona_cd, assembly) -> int | None     # 1 = first term in that Assembly

The KNA member files (members_17.parquet to members_22.parquet in KBL_DATA)
carry `reelection` (초선, 재선, 3선, ...). That field is the member's lifetime
number of terms when the data were collected, and it has the same value in
every Assembly the member sat in. It is not seniority at an Assembly (pitfall
4 in knowledge/data_pitfalls.md, the Paper E Version 1 error).

Derivation. With L the lifetime count, n the number of Assemblies among the
files the member sat in, and k the rank of Assembly a among them (1 for the
earliest), the term number at a is

    L - n + k

because every term the files do not cover came before the first file (the
files run to the current Assembly). kna version 0.7.0 added `term_number`
(and a per-Assembly `seniority` label) to the member files. term_numbers()
uses kna's field wherever it is present and the derivation otherwise, and
check_against_kna() reports where the two disagree. A derived value below 1
means the lifetime count is smaller than the terms the files show, and the
row is flagged instead of trusted.

Usage:
    python3 kna_seniority.py --check          # derived vs kna term_number, per Assembly
    python3 kna_seniority.py MONA_CD ASSEMBLY # one member-term
"""

import argparse
import os
import re
import sys
from pathlib import Path

ASSEMBLIES = tuple(range(17, 23))
MEMBER_FILE = "members_{a}.parquet"
KEY = "mona_cd"

_CACHE: dict = {}


def lifetime_count(label) -> int | None:
    """1 for 초선, 2 for 재선, N for 'N선'. None for anything else."""
    s = str(label or "").strip()
    if s == "초선":
        return 1
    if s == "재선":
        return 2
    m = re.fullmatch(r"(\d+)\s*선", s)
    return int(m.group(1)) if m else None


def data_dir(path=None) -> Path:
    """KBL_DATA (required, there is no default location)."""
    p = path or os.environ.get("KBL_DATA")
    if not p:
        raise RuntimeError("KBL_DATA is not set. Point it at the KNA processed-data directory.")
    return Path(p).expanduser()


def load_members(path=None, assemblies=ASSEMBLIES):
    """One row per member-term from the member files: mona_cd, member_name,
    assembly, reelection, and term_number where the file carries it."""
    import pandas as pd
    import pyarrow.parquet as pq
    d = data_dir(path)
    frames = []
    for a in assemblies:
        f = d / MEMBER_FILE.format(a=a)
        if not f.exists():
            continue
        names = set(pq.ParquetFile(f).schema_arrow.names)
        cols = [c for c in (KEY, "member_name", "reelection", "term_number") if c in names]
        m = pd.read_parquet(f, columns=cols)
        m["assembly"] = a
        frames.append(m)
    if not frames:
        raise FileNotFoundError(f"no member files ({MEMBER_FILE.format(a='NN')}) in the KBL_DATA directory")
    return pd.concat(frames, ignore_index=True)


def derive(members):
    """Add lifetime, n_terms_in_files, rank and term_number_derived to a
    member-term table with mona_cd, assembly and reelection columns."""
    m = members.copy()
    m["lifetime"] = m["reelection"].map(lifetime_count)
    m = m.sort_values([KEY, "assembly"], kind="mergesort")
    m["n_terms_in_files"] = m.groupby(KEY)["assembly"].transform("size")
    m["rank"] = m.groupby(KEY).cumcount() + 1
    m["term_number_derived"] = m["lifetime"] - m["n_terms_in_files"] + m["rank"]
    m.loc[m["lifetime"].isna(), "term_number_derived"] = None
    return m


def term_numbers(path=None, members=None):
    """One row per member-term: mona_cd, assembly, term_number (kna's field
    when present, else derived), term_number_derived, source ('kna' or
    'derived') and problem (non-constant lifetime count, derived value below
    1, unparsed label, or None)."""
    import pandas as pd
    m = derive(members if members is not None else load_members(path))
    kna = m["term_number"] if "term_number" in m else pd.Series([None] * len(m), index=m.index)
    has_kna = kna.notna()
    m["term_number"] = kna.where(has_kna, m["term_number_derived"])
    m["source"] = ["kna" if h else "derived" for h in has_kna]
    varying = m.groupby(KEY)["lifetime"].transform("nunique") > 1
    problems = []
    for vary, life, der in zip(varying, m["lifetime"], m["term_number_derived"]):
        if pd.isna(life):
            problems.append("reelection label not parsed")
        elif vary:
            problems.append("lifetime count differs across Assemblies")
        elif der < 1:
            problems.append("derived term number below 1")
        else:
            problems.append(None)
    m["problem"] = problems
    cols = [KEY] + (["member_name"] if "member_name" in m else []) + \
        ["assembly", "reelection", "term_number", "term_number_derived", "source", "problem"]
    return m[cols].reset_index(drop=True)


def check_against_kna(table) -> dict:
    """Counts of derived versus kna term numbers on the rows where kna's field
    exists, plus up to 20 disagreeing rows."""
    rows = table[table["source"] == "kna"]
    same = rows["term_number"] == rows["term_number_derived"]
    bad = rows[~same]
    return {"member_terms": int(len(table)), "members": int(table[KEY].nunique()),
            "compared": int(len(rows)), "equal": int(same.sum()), "disagree": int((~same).sum()),
            "problems": int(table["problem"].notna().sum()),
            "disagreeing_rows": bad.head(20).to_dict("records")}


def _table(path=None):
    key = str(data_dir(path).resolve())
    if key not in _CACHE:
        _CACHE[key] = term_numbers(path)
    return _CACHE[key]


def term_number(mona_cd: str, assembly: int, path=None) -> int | None:
    """Term number of one member in one Assembly (1 = first term), or None
    when the member did not sit in that Assembly or the row has a problem."""
    t = _table(path)
    hit = t[(t[KEY] == mona_cd) & (t["assembly"] == int(assembly))]
    if hit.empty or hit.iloc[0]["problem"] is not None:
        return None
    v = hit.iloc[0]["term_number"]
    return None if v is None or v != v else int(v)


def first_term(mona_cd: str, assembly: int, path=None) -> bool | None:
    """True when the member was in a first term in that Assembly."""
    n = term_number(mona_cd, assembly, path)
    return None if n is None else n == 1


def _ordinal(n: int) -> str:
    suffix = "th" if 10 <= n % 100 <= 20 else {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suffix}"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Seniority at an Assembly from the KNA member files")
    ap.add_argument("mona_cd", nargs="?")
    ap.add_argument("assembly", nargs="?", type=int)
    ap.add_argument("--check", action="store_true", help="compare the derivation with kna's term_number")
    args = ap.parse_args(argv)
    if args.check:
        t = term_numbers()
        r = check_against_kna(t)
        print(f"member-terms {r['member_terms']}, members {r['members']}, compared with kna term_number "
              f"{r['compared']}, equal {r['equal']}, disagree {r['disagree']}, flagged rows {r['problems']}")
        for a in ASSEMBLIES:
            s = t[t["assembly"] == a]
            if len(s):
                print(f"  {_ordinal(a)}: {len(s)} members, first term {int((s['term_number'] == 1).sum())}, "
                      f"reelection read as 초선 {int((s['reelection'] == '초선').sum())}")
        for row in r["disagreeing_rows"]:
            print(f"  disagree: {row}")
        return 0 if r["disagree"] == 0 else 1
    if not args.mona_cd or args.assembly is None:
        ap.print_help()
        return 1
    print(term_number(args.mona_cd, args.assembly))
    return 0


if __name__ == "__main__":
    sys.exit(main())
