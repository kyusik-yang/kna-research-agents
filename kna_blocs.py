#!/usr/bin/env python3
"""Party-bloc coding for KNA data: one tested, date-indexed source of truth.

    bloc(party_label, date) -> "ruling" | "opposition" | None

"ruling" means the label's party belonged, on that date, to the lineage of
the sitting president's party. Every other party is "opposition". None means
there is no side to assign: an independent (무소속), or a date with no sitting
president (the interregna after the removals of 2017-03-10 and 2025-04-04).
Unknown labels raise UnknownLabelError. Dates the table does not cover raise
CoverageError.

The table is knowledge/party_blocs.csv. Columns:

    kind        party | presidency | independent
    label       party label as it appears in KNA data, or the president's name
    lineage_id  lineage the label's members belong to while the row is valid
                ("conservative" and "democratic" are the two lineages that held
                the presidency in the covered period. Each other party has its
                own id, and the field is empty on an interregnum row)
    relation    main | predecessor | satellite | minor | independent for
                parties (main = current label of a presidential lineage's main
                party, predecessor = an earlier label of that party, satellite =
                a proportional-list satellite, minor = a party outside the two
                presidential lineages), president | acting for presidency rows
    valid_from  first day the row applies (YYYY-MM-DD)
    valid_to    first day it no longer applies (exclusive), empty if open
    successor   label the party became on valid_to (rename or merger), empty
                if it still exists or ended without a recorded successor
    status      needs_confirmation | confirmed
    source      where the row was checked (permanent links)
    checked     date the source was opened
    notes       what the source says, including disagreements between sources

Term-snapshot labels. KNA party fields record the label a member held when the
term began, so a 2023 row can still say 미래통합당 or 미래한국당. bloc() follows
the successor chain from the label's own row to the row valid on the date, so
bloc("미래한국당", "2023-03-01") is "ruling" (미래한국당 -> 미래통합당 ->
국민의힘, Yoon presidency). It codes the label's lineage, not the individual:
a member who left the party (for example a satellite-list member who went back
to a partner party) is coded by the label. See knowledge/data_pitfalls.md.

Reused labels. When one label names two parties (국민의당 2016 and 2020,
정의당 before and after its renames), the row that started most recently on or
before the date is used.

Confirmation (decision D-05). Rows stay needs_confirmation until the researcher
confirms them. Outside tests, bloc() refuses to use an unconfirmed row unless
the caller passes allow_unconfirmed=True, which a caller should only do for a
report that says the coding is provisional.

The module also holds the check functions for the three pitfalls registered in
knowledge/data_pitfalls.md: check_snapshot_labels (term-snapshot party fields),
check_name_identity (merging members by name) and check_passage_definition
(strict versus absorption-inclusive passage).

Usage:
    python3 kna_blocs.py LABEL DATE [--allow-unconfirmed]   # print the side and the chain
    python3 kna_blocs.py --check                             # validate the table
    python3 kna_blocs.py --unconfirmed                       # list rows awaiting confirmation
"""

import csv
import datetime as _dt
import os
import sys
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

BASE_DIR = Path(__file__).parent
TABLE_PATH = BASE_DIR / "knowledge" / "party_blocs.csv"
COLUMNS = ("kind", "label", "lineage_id", "relation", "valid_from", "valid_to",
           "successor", "status", "source", "checked", "notes")
KINDS = ("party", "presidency", "independent")
PARTY_RELATIONS = ("main", "predecessor", "satellite", "minor", "independent")
PRESIDENCY_RELATIONS = ("president", "acting")
STATUSES = ("needs_confirmation", "confirmed")
MAX_CHAIN = 20


class UnknownLabelError(KeyError):
    """The label is not in the table. Add a sourced row rather than guessing."""


class CoverageError(ValueError):
    """The date falls outside what the table covers for this label."""


class UnconfirmedRowError(RuntimeError):
    """A row needed for the answer is still needs_confirmation (D-05)."""


@dataclass(frozen=True)
class Row:
    kind: str
    label: str
    lineage_id: str
    relation: str
    valid_from: _dt.date
    valid_to: "_dt.date | None"
    successor: str
    status: str
    source: str
    checked: str
    notes: str
    line: int

    def contains(self, d):
        return self.valid_from <= d and (self.valid_to is None or d < self.valid_to)


def _as_date(value):
    """Accept a date, a datetime, a pandas Timestamp or an ISO string."""
    if isinstance(value, _dt.datetime):
        return value.date()
    if isinstance(value, _dt.date):
        return value
    if hasattr(value, "date") and callable(value.date):   # pandas Timestamp
        return value.date()
    text = str(value).strip()
    try:
        return _dt.date.fromisoformat(text[:10])
    except ValueError:
        raise ValueError(f"not a date: {value!r} (expected YYYY-MM-DD)") from None


_CACHE = {}


def load_table(path=None):
    """Read the table (cached by path and modification time)."""
    p = Path(path) if path else TABLE_PATH
    key = (str(p), p.stat().st_mtime_ns)
    if key in _CACHE:
        return _CACHE[key]
    rows = []
    with open(p, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        missing = [c for c in COLUMNS if c not in (reader.fieldnames or [])]
        if missing:
            raise ValueError(f"{p}: missing columns {missing}")
        for i, r in enumerate(reader, start=2):
            rows.append(Row(
                kind=r["kind"].strip(), label=r["label"].strip(),
                lineage_id=r["lineage_id"].strip(), relation=r["relation"].strip(),
                valid_from=_as_date(r["valid_from"]),
                valid_to=_as_date(r["valid_to"]) if r["valid_to"].strip() else None,
                successor=r["successor"].strip(), status=r["status"].strip(),
                source=r["source"].strip(), checked=r["checked"].strip(),
                notes=r["notes"].strip(), line=i))
    _CACHE.clear()
    _CACHE[key] = rows
    return rows


def _label_rows(label, rows):
    return sorted((r for r in rows if r.kind in ("party", "independent") and r.label == label),
                  key=lambda r: r.valid_from)


def _tests_running():
    return bool(os.environ.get("PYTEST_CURRENT_TEST"))


def resolve(party_label, date, *, path=None):
    """Return the chain of party rows from the label's own row to the row valid on date."""
    label = str(party_label).strip()
    d = _as_date(date)
    rows = load_table(path)
    own = _label_rows(label, rows)
    if not own:
        raise UnknownLabelError(f"party label {label!r} is not in {path or 'knowledge/party_blocs.csv'}")
    started = [r for r in own if r.valid_from <= d]
    if not started:
        raise CoverageError(f"{label!r} did not exist on {d} (first row starts {own[0].valid_from})")
    row = started[-1]
    chain = [row]
    while not row.contains(d):
        if not row.successor:
            raise CoverageError(f"{label!r}: {row.label} ended {row.valid_to} with no successor recorded, "
                                f"so {d} is not covered")
        nxt = [r for r in _label_rows(row.successor, rows) if r.contains(row.valid_to)]
        if not nxt:
            raise CoverageError(f"table line {row.line}: successor {row.successor!r} has no row valid on {row.valid_to}")
        row = nxt[0]
        chain.append(row)
        if len(chain) > MAX_CHAIN:
            raise CoverageError(f"{label!r}: successor chain longer than {MAX_CHAIN}, check the table")
    return chain


def presidency_row(date, *, path=None):
    """Return the presidency row valid on date (lineage_id empty on an interregnum)."""
    d = _as_date(date)
    hits = [r for r in load_table(path) if r.kind == "presidency" and r.contains(d)]
    if not hits:
        raise CoverageError(f"no presidency row covers {d}")
    return hits[0]


def stale_label(party_label, date, *, path=None):
    """True when the label's own party no longer existed under that label on date."""
    return len(resolve(party_label, date, path=path)) > 1


def _refuse_unconfirmed(rows, allow_unconfirmed):
    if allow_unconfirmed or _tests_running():
        return
    pending = [r for r in rows if r.status != "confirmed"]
    if pending:
        lines = ", ".join(f"{r.label} (line {r.line})" for r in pending)
        raise UnconfirmedRowError(
            f"party_blocs.csv rows still needs_confirmation: {lines}. The researcher confirms rows "
            f"(decision D-05). A provisional report may pass allow_unconfirmed=True and must say so.")


def bloc(party_label, date, *, allow_unconfirmed=False, path=None):
    """Return "ruling", "opposition" or None for a party label on a date."""
    chain = resolve(party_label, date, path=path)
    pres = presidency_row(date, path=path)
    _refuse_unconfirmed(chain + [pres], allow_unconfirmed)
    lineage = chain[-1].lineage_id
    if chain[-1].kind == "independent" or lineage == "none":
        return None
    if not pres.lineage_id:
        return None
    return "ruling" if lineage == pres.lineage_id else "opposition"


def unconfirmed_rows(path=None):
    return [r for r in load_table(path) if r.status != "confirmed"]


def validate_table(path=None):
    """Return a list of problems in the table (empty when it is consistent)."""
    problems = []
    rows = load_table(path)
    for r in rows:
        where = f"line {r.line} ({r.label})"
        if r.kind not in KINDS:
            problems.append(f"{where}: kind {r.kind!r}")
        allowed = PRESIDENCY_RELATIONS if r.kind == "presidency" else PARTY_RELATIONS
        if r.relation not in allowed:
            problems.append(f"{where}: relation {r.relation!r} for kind {r.kind}")
        if r.status not in STATUSES:
            problems.append(f"{where}: status {r.status!r}")
        if not r.source:
            problems.append(f"{where}: no source")
        if r.valid_to is not None and r.valid_to <= r.valid_from:
            problems.append(f"{where}: valid_to {r.valid_to} not after valid_from {r.valid_from}")
        if r.kind == "party" and not r.lineage_id:
            problems.append(f"{where}: party row without lineage_id")
        if r.kind == "presidency" and r.relation == "president" and not r.lineage_id:
            problems.append(f"{where}: president without lineage_id")
        if r.successor:
            if r.valid_to is None:
                problems.append(f"{where}: successor without valid_to")
            elif not [s for s in _label_rows(r.successor, rows) if s.contains(r.valid_to)]:
                problems.append(f"{where}: successor {r.successor!r} has no row valid on {r.valid_to}")
    by_label = defaultdict(list)
    for r in rows:
        if r.kind != "presidency":
            by_label[r.label].append(r)
    for label, rs in by_label.items():
        rs = sorted(rs, key=lambda r: r.valid_from)
        for a, b in zip(rs, rs[1:]):
            if a.valid_to is None or a.valid_to > b.valid_from:
                problems.append(f"{label}: rows at lines {a.line} and {b.line} overlap")
    pres = sorted((r for r in rows if r.kind == "presidency"), key=lambda r: r.valid_from)
    for a, b in zip(pres, pres[1:]):
        if a.valid_to != b.valid_from:
            problems.append(f"presidency rows at lines {a.line} and {b.line} leave a gap or overlap")
    if pres and pres[-1].valid_to is not None:
        problems.append("the last presidency row should be open-ended")
    return problems


# ---------------------------------------------------------------------------
# Pitfall checks (knowledge/data_pitfalls.md)
# ---------------------------------------------------------------------------

def _records(records):
    """Yield (index, dict) from a pandas DataFrame or an iterable of dicts."""
    if hasattr(records, "to_dict") and hasattr(records, "index"):
        for idx, rec in zip(records.index, records.to_dict("records")):
            yield idx, rec
    else:
        for idx, rec in enumerate(records):
            yield idx, rec


def _missing(value):
    return value is None or (isinstance(value, float) and value != value) or str(value).strip() == ""


STATUS_ALIASES = {"ruling": "ruling", "opposition": "opposition", "independent": None,
                  "여당": "ruling", "야당": "opposition", "무소속": None}


def check_snapshot_labels(records, *, party="leg_party", date="date", status="leg_ruling_status",
                          allow_unconfirmed=False, path=None):
    """Pitfall 1 (term-snapshot party fields).

    Flag every row whose recorded ruling status disagrees with bloc(label, date)
    (reason "status_mismatch") and every row whose label had ceased to exist on
    that date (reason "stale_label"). Pass status=None to check labels only.
    Unknown labels are flagged (reason "unknown_label") rather than raised, so
    one call reports the whole frame.
    """
    flags = []
    for idx, rec in _records(records):
        label, d = rec.get(party), rec.get(date)
        if _missing(label) or _missing(d):
            continue
        try:
            expected = bloc(label, d, allow_unconfirmed=allow_unconfirmed, path=path)
            stale = stale_label(label, d, path=path)
        except (UnknownLabelError, CoverageError) as e:
            flags.append({"row": idx, "label": label, "date": str(d)[:10], "recorded": None,
                          "expected": None, "stale": None, "reason": "unknown_label", "detail": str(e)})
            continue
        recorded = None
        if status is not None and not _missing(rec.get(status)):
            raw = str(rec.get(status)).strip()
            recorded = STATUS_ALIASES.get(raw, raw)
            if recorded != expected:
                flags.append({"row": idx, "label": label, "date": str(d)[:10], "recorded": raw,
                              "expected": expected, "stale": stale, "reason": "status_mismatch"})
                continue
        if stale:
            flags.append({"row": idx, "label": label, "date": str(d)[:10], "recorded": recorded,
                          "expected": expected, "stale": True, "reason": "stale_label"})
    return flags


def check_name_identity(records, *, name="leg_name", uid="leg_member_uid", within=("term",)):
    """Pitfall 2 (merging members by name).

    Return one flag per name that maps to more than one member id inside a
    scope (the `within` columns that exist in the records). Each flag is either
    a homonym (two people, as with the two 이수진 of the 21st Assembly) or id
    aliasing (one person under several ids). In both cases merges and groupings
    must key on the id, never on the name.
    """
    ids = defaultdict(set)
    counts = defaultdict(int)
    for _, rec in _records(records):
        n = rec.get(name)
        if _missing(n):
            continue
        scope = tuple((c, rec.get(c)) for c in within if c in rec)
        key = (scope, str(n).strip())
        counts[key] += 1
        if not _missing(rec.get(uid)):
            ids[key].add(str(rec.get(uid)).strip())
    flags = []
    for key, s in ids.items():
        if len(s) > 1:
            scope, n = key
            flags.append({"name": n, "scope": dict(scope), "uids": sorted(s), "n_rows": counts[key]})
    return sorted(flags, key=lambda f: (str(f["scope"]), f["name"]))


STRICT_PASSAGE = frozenset({"원안가결", "수정가결"})
ALTERNATIVE_ABSORBED = frozenset({"대안반영폐기"})
AMENDMENT_ABSORBED = frozenset({"수정안반영폐기"})
PASSAGE_DEFINITIONS = {
    "strict": STRICT_PASSAGE,
    "alternative_inclusive": STRICT_PASSAGE | ALTERNATIVE_ABSORBED,        # the KNA `passed` column
    "absorption_inclusive": STRICT_PASSAGE | ALTERNATIVE_ABSORBED | AMENDMENT_ABSORBED,
}


def passage_rates(statuses):
    """Share of bills passed under each definition, from bill status strings."""
    vals = [str(s).strip() for s in statuses if not _missing(s)]
    n = len(vals)
    out = {"n": n}
    for key, members in PASSAGE_DEFINITIONS.items():
        out[key] = (sum(v in members for v in vals) / n) if n else float("nan")
    out["ratio_absorption_to_strict"] = (out["absorption_inclusive"] / out["strict"]
                                         if n and out["strict"] else float("nan"))
    return out


def check_passage_definition(records, *, flag="passed", status="status"):
    """Pitfall 3 (strict versus absorption-inclusive passage).

    Report which definition a 0/1 passage column encodes ("strict",
    "alternative_inclusive", "absorption_inclusive", or "neither") together with
    the rates under every definition, so an analysis states its definition and
    reports the other one alongside it.
    """
    pairs = [(rec.get(flag), rec.get(status)) for _, rec in _records(records)
             if not _missing(rec.get(flag)) and not _missing(rec.get(status))]
    statuses = [s for _, s in pairs]
    matches = [key for key, members in PASSAGE_DEFINITIONS.items()
               if pairs and all(bool(int(f)) == (str(s).strip() in members) for f, s in pairs)]
    return {"column": flag, "matches": matches[0] if matches else "neither",
            "all_matches": matches, "rates": passage_rates(statuses), "n": len(pairs)}


def _main(argv):
    if argv[:1] == ["--check"]:
        problems = validate_table()
        for p in problems:
            print(p)
        print(f"{len(load_table())} rows, {len(problems)} problems")
        return 1 if problems else 0
    if argv[:1] == ["--unconfirmed"]:
        for r in unconfirmed_rows():
            print(f"line {r.line}: {r.kind} {r.label} {r.valid_from}..{r.valid_to or ''} ({r.status})")
        return 0
    allow = "--allow-unconfirmed" in argv
    args = [a for a in argv if a != "--allow-unconfirmed"]
    if len(args) != 2:
        print(__doc__)
        return 2
    label, date = args
    try:
        chain = resolve(label, date)
        pres = presidency_row(date)
        for r in chain:
            print(f"  {r.label} [{r.lineage_id}, {r.relation}] {r.valid_from}..{r.valid_to or ''} -> {r.successor or '-'}")
        print(f"  president: {pres.label} [{pres.lineage_id or 'none'}]")
        print(bloc(label, date, allow_unconfirmed=allow))
    except (UnknownLabelError, CoverageError, UnconfirmedRowError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 3
    return 0


if __name__ == "__main__":
    sys.exit(_main(sys.argv[1:]))
