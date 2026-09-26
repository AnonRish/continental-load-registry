#!/usr/bin/env python3
"""
One-time migration from monolithic data/facility_records/<RTO>.json files to
small indexed shards.

This script is intentionally separate from the normal builder so the migration
can run once against the already-published record files. It also patches the
static dashboard loader to resolve a facility ID through the RTO index and then
fetch only the shard containing that record.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

from build_facility_records import SHARD_SIZE, write_sharded_rto

ROOT = Path(".")
RECORDS = ROOT / "data" / "facility_records"
HTML = ROOT / "index.html"

RTO_FILES = {
    "AESO", "CAISO", "ERCOT", "IESO", "ISO-NE", "MISO", "NYISO", "PJM", "SPP"
}

NEW_LOADER = r"""const researchRecordIndexCache = new Map();
const RECORD_STORAGE_VERSION = '2';

async function fetchResearchJson(url){
  const response = await fetch(url + '?v=' + RECORD_STORAGE_VERSION, {cache:'no-store'});
  if(!response.ok) throw new Error('Research record resource unavailable ('+response.status+')');
  return response.json();
}
async function loadResearchRecord(r){
  if(researchRecordCache.has(r.id)) return researchRecordCache.get(r.id);
  let rtoIndex = researchRecordIndexCache.get(r.rto);
  if(!rtoIndex){
    rtoIndex = await fetchResearchJson('data/facility_records/'+encodeURIComponent(r.rto)+'/index.json');
    if(!rtoIndex || rtoIndex.schema_version !== 2 || !rtoIndex.lookup) throw new Error('Invalid research-record index');
    researchRecordIndexCache.set(r.rto, rtoIndex);
  }
  const shardPath = rtoIndex.lookup[r.id];
  if(!shardPath) throw new Error('Facility record not found in RTO index');
  const payload = await fetchResearchJson(shardPath);
  normalizeLookupPayload(payload);
  const rec = researchRecordCache.get(r.id);
  if(!rec) throw new Error('Facility record not found in shard');
  return rec;
}
"""

def main() -> int:
    RECORDS.mkdir(parents=True, exist_ok=True)

    migrated = 0
    for rto in sorted(RTO_FILES):
        legacy = RECORDS / f"{rto}.json"
        if not legacy.exists():
            continue
        payload = json.loads(legacy.read_text(encoding="utf-8"))
        records = payload.get("records")
        if not isinstance(records, list):
            raise SystemExit(f"{legacy}: expected a records array")
        write_sharded_rto(RECORDS, rto, records)
        legacy.unlink()
        migrated += 1

    # Rebuild the small top-level index from the generated RTO indexes.
    rto_counts = {}
    files = {}
    for rto in sorted(RTO_FILES):
        idx_path = RECORDS / rto / "index.json"
        if not idx_path.exists():
            continue
        idx = json.loads(idx_path.read_text(encoding="utf-8"))
        rto_counts[rto] = int(idx["record_count"])
        files[rto] = f"data/facility_records/{rto}/index.json"

    top = {
        "schema_version": 2,
        "record_count": sum(rto_counts.values()),
        "rto_counts": rto_counts,
        "shard_size": SHARD_SIZE,
        "files": files,
    }
    (RECORDS / "index.json").write_text(json.dumps(top, indent=2) + "\n", encoding="utf-8")

    html = HTML.read_text(encoding="utf-8")
    pattern = re.compile(
        r"const researchRecordCache = new Map\(\);.*?function renderResearchRecord",
        re.S,
    )
    # The cache declaration belongs immediately before normalizeLookupPayload;
    # preserve that function and everything after it.
    current = pattern.search(html)
    if not current:
        raise SystemExit("could not find the research-record loader block in index.html")

    replacement = (
        "const researchRecordCache = new Map();\n"
        "\n"
        "function humanFieldName"  # marker removed below; used only to fail safely
    )
    # Replace only the loader/cache segment from cache declaration through the
    # function immediately preceding renderResearchRecord.
    cache_start = html.find("const researchRecordCache = new Map();")
    render_start = html.find("function renderResearchRecord", cache_start)
    if cache_start < 0 or render_start < 0:
        raise SystemExit("could not locate research-record loader boundaries")
    block = html[cache_start:render_start]

    # Keep normalizeLookupPayload and everything before the old loader, then
    # replace the cache + old loader portion with the sharded implementation.
    norm_start = block.find("function normalizeLookupPayload")
    if norm_start < 0:
        raise SystemExit("normalizeLookupPayload not found")
    normalize_fn = block[norm_start:block.find("async function loadResearchRecord", norm_start)]
    new_block = "const researchRecordCache = new Map();\n\n" + normalize_fn + NEW_LOADER + "\n"
    html = html[:cache_start] + new_block + html[render_start:]

    html = html.replace(
        "data/facility_records/'+encodeURIComponent(r.rto)+'.json",
        "data/facility_records/'+encodeURIComponent(r.rto)+'/index.json",
    )
    if "data/facility_records/'+encodeURIComponent(r.rto)+'.json" in html:
        raise SystemExit("legacy monolithic RTO link remains in index.html")
    if "RECORD_STORAGE_VERSION = '2'" not in html:
        raise SystemExit("sharded record loader marker missing from index.html")

    HTML.write_text(html, encoding="utf-8")

    print(f"Migrated {migrated} monolithic RTO record files to shards.")
    print(f"Published records indexed: {top['record_count']}")
    for rto, count in sorted(rto_counts.items()):
        print(f"{rto:7s} {count:4d} records")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
