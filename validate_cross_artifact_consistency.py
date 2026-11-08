#!/usr/bin/env python3
"""Fail when a count copied between public artifacts disagrees with its owner.

This is the plain-Python entry point used by the sync workflows. It runs the
cross-artifact contracts in tests/test_public_surface.py (one source of truth,
no pytest needed). None of them hard-code a count that the daily syncs change:
each copied number is compared with the file that owns it.
"""
from __future__ import annotations

import importlib.util
import sys
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parent

CONTRACTS = (
    "test_derived_counts_match_their_owners",
    "test_large_load_accounting",
    "test_project_and_supplemental_layers",
    "test_manifests_describe_the_same_layers",
    "test_bpa_layer_contract",
    "test_queue_snapshots_agree_with_their_status",
    "test_registry_shards_cover_the_registry",
    "test_track3_ledgers_reconcile",
    "test_public_web_claims_mirror_their_source",
    "test_catalog_lists_only_real_files",
    "test_homepage_project_counts_match_the_project_layer",
    "test_storage_rows_carry_no_compute_estimates",
)


def main() -> int:
    spec = importlib.util.spec_from_file_location("public_surface", ROOT / "tests" / "test_public_surface.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    failures = 0
    for name in CONTRACTS:
        try:
            getattr(module, name)()
        except AssertionError as exc:
            failures += 1
            detail = str(exc) or traceback.format_exc(limit=-1).strip().splitlines()[-2]
            print(f"FAIL {name}: {detail[:1500]}")
        else:
            print(f"ok   {name}")
    rows = module.registry_rows()
    print(f"core registry: {len(rows)} rows, {sum(float(r['mw']) for r in rows) / 1000:.4f} GW")
    if failures:
        print(f"FAIL: {failures} of {len(CONTRACTS)} cross-artifact contracts")
        return 1
    print(f"PASS: all {len(CONTRACTS)} cross-artifact contracts")
    return 0


if __name__ == "__main__":
    sys.exit(main())
