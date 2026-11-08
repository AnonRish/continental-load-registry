#!/usr/bin/env python3
"""Run every offline check in this repository and print one verdict.

    pip install -r requirements.txt
    python verify.py            # everything (about a minute)
    python verify.py --quick    # skip the slower self-tests

Nothing here touches the network or rewrites a tracked file; the last check
confirms that. CI runs exactly this command on every push and pull request.
"""
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PY = sys.executable
TMP = Path(tempfile.mkdtemp(prefix="clr-verify-"))

# (label, command, slow). Commands run from the repository root.
CHECKS: list[tuple[str, list[str], bool]] = [
    ("unit and contract tests", [PY, "-m", "pytest", "-q", "-p", "no:cacheprovider", "tests", "track3"], False),
    # pipeline self-tests (synthetic fixtures; no network)
    ("ingest self-test", [PY, "scripts/ingest_grid_queues.py", "--selftest"], True),
    ("compute-estimate self-test", [PY, "scripts/compute_anomaly_detector.py", "--selftest"], False),
    ("ambiguous-load investigator self-test", [PY, "scripts/investigate_ambiguous_loads.py", "--selftest"], True),
    ("registry refresh guard self-test", [PY, "scripts/guard_registry_refresh.py", "--selftest"], False),
    ("Epoch sync self-test", [PY, "scripts/sync_epoch_ai_data_centers.py", "--selftest"], False),
    ("compute-universe parser self-test", [PY, "scripts/sync_global_compute_sources.py", "--selftest"], False),
    ("Track 3 source-map self-test", [PY, "scripts/sync_track3_external_sources.py", "--selftest"], False),
    ("Module 1 radar self-test", [PY, "scripts/module1_physical_radar.py", "--selftest"], False),
    # Track 3 calculators on their published example inputs
    ("residual bound example", [PY, "scripts/track3_bound.py", "--input", "data/track3/residual_bound_input.example.json"], False),
    ("tail audit example", [PY, "scripts/track3_tail_audit.py", "--input", "data/track3/tail_audit_input.example.json",
                            "--sample-size", "3", "--seed", "track3-example"], False),
    ("audit chain example", [PY, "scripts/track3_audit_chain.py", "--input", "data/track3/audit_chain_input.example.json"], False),
    ("H100e unit conversion", [PY, "scripts/track3_units.py", "--h100e", "30000", "--year", "2028.6"], False),
    ("certificate calculator", [PY, "scripts/track3_certificate.py", "--tail-units", "1000", "--sample-size", "50",
                                "--failures", "0", "--delta", "0.05", "--write-json", str(TMP / "certificate.json")], False),
    ("independent Track 3 verifier", [PY, "scripts/verify_track3.py"], False),
    # reproducibility and cross-artifact contracts
    ("derived counts match their owners", [PY, "scripts/refresh_derived_counts.py", "--check"], False),
    ("cross-artifact consistency", [PY, "scripts/validate_cross_artifact_consistency.py"], False),
    ("Track 3 ledger joins", [PY, "scripts/validate_track3_ledger.py"], False),
    ("Track 3 complete coverage", [PY, "scripts/validate_track3_complete_coverage.py"], False),
    ("Track 3 release consistency", [PY, "scripts/validate_track3_release.py"], False),
    ("physical provenance manifest reproducible", [PY, "scripts/build_physical_provenance_manifest.py", "--check"], False),
    ("physical provenance contracts", [PY, "scripts/validate_physical_provenance.py"], False),
    ("ambiguous case studies", [PY, "scripts/validate_ambiguous_case_studies.py"], False),
    ("strict discovery candidates", [PY, "scripts/validate_strict_discovery_candidates.py"], False),
    ("ambiguity classification summary reproducible", [PY, "scripts/build_ambiguity_classification_summary.py", "--check"], False),
]


def tracked_state() -> str | None:
    if not (ROOT / ".git").exists() or shutil.which("git") is None:
        return None
    return subprocess.run(["git", "status", "--porcelain", "--untracked-files=no"], cwd=ROOT,
                          capture_output=True, text=True).stdout


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--quick", action="store_true", help="skip the slower pipeline self-tests")
    ap.add_argument("-v", "--verbose", action="store_true", help="print the output of every check")
    args = ap.parse_args()

    try:
        import pytest  # noqa: F401
    except ImportError:
        print("pytest is missing: pip install -r requirements.txt")
        return 2

    before = tracked_state()
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", PYTHONUNBUFFERED="1")
    failed: list[str] = []
    started = time.time()
    for label, cmd, slow in CHECKS:
        if slow and args.quick:
            print(f"  skip  {label}")
            continue
        if not (ROOT / cmd[1]).exists() and cmd[1] != "-m":
            failed.append(label)
            print(f"  FAIL  {label}: {cmd[1]} not found")
            continue
        t0 = time.time()
        proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, env=env)
        ok = proc.returncode == 0
        print(f"  {'ok  ' if ok else 'FAIL'}  {label}  ({time.time() - t0:.1f}s)")
        if not ok or args.verbose:
            tail = (proc.stdout[-3000:] + proc.stderr[-3000:]).strip()
            print("\n".join("        " + line for line in tail.splitlines()[-40:]))
        if not ok:
            failed.append(label)

    after = tracked_state()
    if before is not None and after != before:
        failed.append("checks left tracked files unchanged")
        print("  FAIL  checks left tracked files unchanged:")
        print("\n".join("        " + line for line in after.splitlines()[:20]))
    shutil.rmtree(TMP, ignore_errors=True)

    total = len([c for c in CHECKS if not (c[2] and args.quick)])
    if failed:
        print(f"\nFAIL: {len(failed)} of {total} checks failed ({time.time() - started:.0f}s): " + "; ".join(failed))
        return 1
    print(f"\nPASS: all {total} checks passed ({time.time() - started:.0f}s).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
