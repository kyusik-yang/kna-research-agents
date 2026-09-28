# Paper D, Version 2 replication (2026-09-26). Rebuilds dyads21_meta.parquet,
# the intermediate that r25/build.py, r25/recode.py and r26/build_cohort3.py
# read. It is the 21st-Assembly subset of the kr-hearings dyads release with
# the metadata columns only (no speech text). The Arc 4 analyst built the file
# interactively and saved no script, so this script was written for the
# replication package. On 2026-09-26 its output matched the stored file row for
# row and column for column (pandas DataFrame.equals).
# Run from the package root, with the release in data/.
import pyarrow.parquet as pq

COLS = ["meeting_id", "term", "committee", "committee_key", "hearing_type", "date", "agenda",
        "leg_name", "leg_member_uid", "leg_party", "leg_ruling_status", "witness_name",
        "witness_role", "witness_affiliation", "witness_ministry_normalized", "direction"]

d = pq.read_table("data/dyads_16_22_v9.parquet", columns=COLS, filters=[("term", "=", 21)]).to_pandas()
d.to_parquet("dyads21_meta.parquet")
print("dyads21_meta.parquet:", len(d), "rows,", len(d.columns), "columns")
