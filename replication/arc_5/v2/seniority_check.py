# Paper E version 2. Is first_term (reelection == '초선') the seniority at each Assembly?
# Run from the replication package root: KBL_DATA=<kna processed dir> python3 v2/seniority_check.py
# The KNA codebook documents `reelection` as lifetime seniority at collection.
# Derive seniority at each Assembly from the KBL_DATA member files alone:
#   term_number(a) = (lifetime count L) - (terms served in 17-22) + rank of a among them
# and compare with the reelection-based indicator. Optionally validate the
# derivation against a KNA build directory that carries term_number (argv[1]).
import os, sys, re
import pandas as pd
D = os.environ["KBL_DATA"]
rows = []
for a in range(17, 23):
    m = pd.read_parquet(f"{D}/members_{a}.parquet", columns=["mona_cd", "member_name", "reelection"])
    m["assembly"] = a
    rows.append(m)
m = pd.concat(rows, ignore_index=True)
def lifetime(s):
    if s == "초선": return 1
    if s == "재선": return 2
    mm = re.match(r"(\d+)선", str(s))
    return int(mm.group(1)) if mm else None
m["L"] = m["reelection"].map(lifetime)
# L should be constant per member across assemblies
nL = m.groupby("mona_cd")["L"].nunique()
print("members with non-constant lifetime count:", int((nL > 1).sum()), "of", len(nL))
m = m.sort_values(["mona_cd", "assembly"])
m["n_1722"] = m.groupby("mona_cd")["assembly"].transform("size")
m["rank"] = m.groupby("mona_cd").cumcount() + 1
m["term_number_derived"] = m["L"] - m["n_1722"] + m["rank"]
print("derived term_number < 1:", int((m.term_number_derived < 1).sum()))
m["ft_reelection"] = (m["reelection"] == "초선").astype(int)
m["ft_derived"] = (m["term_number_derived"] == 1).astype(int)
t = m.groupby("assembly").agg(members=("mona_cd", "size"), ft_reelection=("ft_reelection", "sum"),
                              ft_derived=("ft_derived", "sum"),
                              disagree=("ft_reelection", lambda s: int((s != m.loc[s.index, "ft_derived"]).sum())))
print(t)
if len(sys.argv) > 1:
    v = []
    for a in range(17, 23):
        x = pd.read_parquet(f"{sys.argv[1]}/members_{a}.parquet", columns=["mona_cd", "term_number"])
        x["assembly"] = a
        v.append(x)
    v = pd.concat(v)
    j = m.merge(v, on=["mona_cd", "assembly"], how="left")
    print("validation rows matched:", int(j.term_number.notna().sum()), "of", len(j))
    j2 = j[j.term_number.notna()]
    print("term_number equal:", int((j2.term_number == j2.term_number_derived).sum()), "of", len(j2))
    print("first-term flag equal:", int(((j2.term_number == 1).astype(int) == j2.ft_derived).sum()), "of", len(j2))
    bad = j2[j2.term_number != j2.term_number_derived]
    print(bad[["assembly", "member_name", "reelection", "term_number", "term_number_derived"]].head(20).to_string())
OUT = os.environ.get("PAPER_E_OUT", "v2")
m[["mona_cd", "assembly", "reelection", "L", "n_1722", "term_number_derived", "ft_reelection", "ft_derived"]].to_csv(
    os.path.join(OUT, "seniority_derived.csv"), index=False)
