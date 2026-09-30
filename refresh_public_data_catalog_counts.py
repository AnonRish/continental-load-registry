#!/usr/bin/env python3
"""Keep generated-file counts in data/public_data_catalog.json in sync with the files.

Catalog counts for generated artifacts were hand-edited, so they drifted from the
ledger every time the automated pipeline rebuilt it. This derives them instead.

    python refresh_public_data_catalog_counts.py          # rewrite counts
    python refresh_public_data_catalog_counts.py --check  # exit 1 on any drift or missing file
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CATALOG = ROOT / "data/public_data_catalog.json"
# catalog path -> key inside the file that holds the authoritative count
DERIVED = {"data/track3/evidence_records.json": "record_count"}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    cat = json.loads(CATALOG.read_text(encoding="utf-8"))
    problems = []
    for d in cat["datasets"]:
        path = ROOT / d["path"]
        if not path.exists():
            problems.append(f"catalog lists a file that does not exist: {d['path']}")
            continue
        key = DERIVED.get(d["path"])
        if key:
            actual = json.loads(path.read_text(encoding="utf-8"))[key]
            if d.get("record_count") != actual:
                problems.append(f"{d['path']}: catalog says {d.get('record_count')}, file says {actual}")
                if not args.check:
                    d["record_count"] = actual
    if args.check:
        for msg in problems:
            print("DRIFT:", msg)
        return 1 if problems else 0
    CATALOG.write_text(json.dumps(cat, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    for msg in problems:
        print("NOTE:", msg)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
