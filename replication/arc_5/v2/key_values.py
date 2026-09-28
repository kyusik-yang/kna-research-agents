# Paper E version 2: flatten the numbers the paper reports into one JSON file,
# so that replicate.py verify can compare a rerun against them.
# Run from the replication package root after v2/tables_v2.py and
# v2/recode_tables_v2.py:  python3 v2/key_values.py
import json
import os
from pathlib import Path

OUTDIR = Path(os.environ.get("PAPER_E_OUT", "v2"))
t = json.loads((OUTDIR / "tables_v2.json").read_text(encoding="utf-8"))
r = json.loads((OUTDIR / "recode_tables_v2.json").read_text(encoding="utf-8"))
flat = {}


def walk(prefix, obj):
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k.startswith("_"):
                continue
            walk(f"{prefix}.{k}" if prefix else str(k), v)
    elif isinstance(obj, bool):
        return
    elif isinstance(obj, (int, float)):
        flat[prefix] = obj


walk("t", t)
walk("r", r)
(OUTDIR / "key_values.json").write_text(json.dumps(flat, ensure_ascii=False, indent=1, sort_keys=True) + "\n",
                                        encoding="utf-8")
print(f"wrote {len(flat)} values to {OUTDIR / 'key_values.json'}")
