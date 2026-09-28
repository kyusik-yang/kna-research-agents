#!/usr/bin/env bash
# Build a read-only copy of the kna v0.6.0 data for reproducing the papers
# published before kna 0.7.0 (see KNA_070_PUBLISHED.md).
#
# The copy is a detached git worktree of the kna repository at tag v0.6.0,
# with its Git LFS files pulled. The kna checkout itself is not modified
# (git records the extra worktree in its metadata only). The script also
# writes member_info_17_22.parquet, which the round 22 and round 30 figure
# scripts read. kna never tracked that file. It is rebuilt here as the
# concatenation of members_17..22 plus the alias columns assembly (= age)
# and gender (= sex). The September 2026 audit found the forum's own copy
# equal to this concatenation.
#
# Usage:
#   scripts/setup_kna_v060.sh <path to the kna repository> <new directory>
#   export KNA_DATA_V060=<new directory>/data/processed
set -euo pipefail

if [ $# -ne 2 ]; then
  echo "usage: $0 <kna repository> <new directory>" >&2
  exit 2
fi
KNA_REPO=$1
TARGET=$2

if [ -e "$TARGET" ]; then
  echo "$TARGET already exists. Choose a new directory." >&2
  exit 1
fi
if ! git -C "$KNA_REPO" rev-parse -q --verify 'v0.6.0^{commit}' >/dev/null; then
  git -C "$KNA_REPO" fetch origin tag v0.6.0 --no-tags
fi
command -v git-lfs >/dev/null || { echo "git-lfs is required (brew install git-lfs)" >&2; exit 1; }

git -C "$KNA_REPO" worktree add --detach "$TARGET" v0.6.0
git -C "$TARGET" lfs pull

python3 - "$TARGET/data/processed" <<'EOF'
import sys
from pathlib import Path

import pandas as pd

d = Path(sys.argv[1])
frames = [pd.read_parquet(d / f"members_{a}.parquet") for a in range(17, 23)]
m = pd.concat(frames, ignore_index=True)
m["assembly"] = m["age"]
m["gender"] = m["sex"]
assert len(m) == 1933 and "term_number" not in m.columns, "unexpected v0.6.0 member files"
m.to_parquet(d / "member_info_17_22.parquet", index=False)
print(f"wrote {d / 'member_info_17_22.parquet'} ({len(m)} rows, {m.shape[1]} columns)")
EOF

echo
echo "Done. Set:"
echo "  export KNA_DATA_V060=$TARGET/data/processed"
