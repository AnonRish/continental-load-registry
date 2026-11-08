"""Contracts for the public site and its data files.

These run offline against the committed snapshot. Counts that the daily syncs
change are never written here as literals: each test compares a copied number
with the file that owns it, so a correct refresh can never fail CI and a stale
copy always does.
"""
from __future__ import annotations

import csv
import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SITE = "https://anonrish.github.io/continental-load-registry/"
REGISTRY_RE = re.compile(r"const REGISTRY_DATA = (\[.*?\]);\n", re.S)


def load(rel: str):
    return json.loads((ROOT / rel).read_text(encoding="utf-8"))


def read_csv(rel: str) -> list[dict[str, str]]:
    with (ROOT / rel).open(encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def text(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def registry_rows() -> list[dict]:
    match = REGISTRY_RE.search(text("index.html"))
    assert match, "index.html: REGISTRY_DATA block not found"
    return json.loads(match.group(1))


def reference_universe_size() -> int:
    """The frozen Track 3 reference universe (see sync_epoch_ai_data_centers.py)."""
    return len(load("data/external/epoch_ai/site_level_connection_evidence.json")["records"])


def pages() -> list[Path]:
    return sorted(ROOT.glob("*.html"))


# --------------------------------------------------------------------------- data


def test_derived_counts_match_their_owners():
    proc = subprocess.run(["python3", str(ROOT / "refresh_derived_counts.py"), "--check"],
                          cwd=ROOT, capture_output=True, text=True)
    assert proc.returncode == 0, proc.stdout[-4000:] + proc.stderr[-2000:]


def test_plan_a_machine_readable_files():
    for rel in ("data/track3/ai2040_plan_a_mapping.json", "data/track3/ai2040_plan_a_traceability.json",
                "data/track3/plan_a_audit_schema.json", "data/track3_evidence_schema.json"):
        assert load(rel), rel
    assert len(load("data/track3/ai2040_plan_a_mapping.json")["mappings"]) >= 16
    assert len(load("data/track3/ai2040_plan_a_traceability.json")["rows"]) >= 12
    assert len(load("data/track3_evidence_schema.json")["domains"]) >= 15


def test_large_load_accounting():
    d = load("data/large_load_scope.json")["definitions"]
    rows = registry_rows()
    assert d["current_row_level"]["records"] == len(rows) > 0
    assert abs(d["current_row_level"]["capacity_gw"] - sum(float(r["mw"]) for r in rows) / 1000) < 1e-6
    extra = d["additional_known_miso"]
    assert d["expanded_known_scope"]["records"] == d["current_row_level"]["records"] + extra["records"]
    assert abs(d["expanded_known_scope"]["capacity_gw"]
               - (d["current_row_level"]["capacity_gw"] + float(extra["capacity_gw"]))) < 1e-6
    history = load("data/caiso_cluster_history.json")["records"]
    report_2024 = [r for r in history if r.get("source_year") == 2024]
    assert d["caiso_historical_cluster_series"]["records"] == sum(r["projects"] for r in report_2024)
    assert abs(d["caiso_historical_cluster_series"]["capacity_gw"] - sum(r["capacity_mw"] for r in report_2024) / 1000) < 1e-9


def test_project_and_supplemental_layers():
    projects = load("data/project_level_extractions.json")
    ids = [r["id"] for r in projects["records"]]
    assert projects["record_count"] == len(ids) == len(set(ids)) > 0
    for r in projects["records"]:
        assert r["id"] and r["evidence_type"] and r["source_url"].startswith("https://"), r["id"]
    project_map = load("data/project_level_map.json")
    assert project_map["record_count"] == len(project_map["records"]) == project_map["mapped_count"]
    assert {r["id"] for r in project_map["records"]} == set(ids)
    assert all(r.get("lat") is not None and r.get("lon") is not None for r in project_map["records"])
    woostor = next(r for r in projects["records"] if r["id"] == "ALABAMA-POWER-WOOSTOR-CONTRACT-2026")
    assert not woostor.get("location"), "the one unlocated contract must stay unpinned"

    supplemental = load("data/supplemental_large_load_evidence.json")
    supp_ids = [r["id"] for r in supplemental["records"]]
    assert supplemental["record_count"] == len(supp_ids) == len(set(supp_ids)) > 0
    aggregate = load("data/supplemental_aggregate_map.json")
    assert aggregate["record_count"] == len(aggregate["records"]) == aggregate["mapped_count"] > 0
    assert all(r.get("lat") is not None and r.get("lon") is not None for r in aggregate["records"])


def test_manifests_describe_the_same_layers():
    manifest = load("data/market_universe_manifest.json")
    checklist = load("data/data_universe_checklist.json")
    assert {m["id"] for m in manifest["markets"]} == {m["id"] for m in read_csv("data/market_universe_manifest.csv")}
    assert len(checklist["records"]) == len(read_csv("data/data_universe_checklist.csv")) == len(manifest["markets"])
    layers = load("data/map_layer_manifest.json")["layers"]
    assert [x["id"] for x in layers] == [x["id"] for x in read_csv("data/map_layer_manifest.csv")]
    by_id = {x["id"]: x for x in layers}
    assert by_id["SUPPLEMENTAL_EVIDENCE"]["mapped_records"] is None
    for layer in layers:
        if layer.get("file") and not (ROOT / layer["file"]).exists():
            # Allowed only when the layer says so (e.g. NYISO before its first successful capture).
            assert str(layer.get("status", "")).startswith("snapshot not currently present"), (
                f"map layer {layer['id']} points at a missing file without saying so")


def test_bpa_layer_contract():
    bpa = load("data/bpa_large_load_registry.json")
    records = bpa["records"]
    mapped = [r for r in records if isinstance(r.get("map_point"), list) and len(r["map_point"]) == 2]
    assert bpa["record_count"] == len(records) > 0
    assert bpa["mapped_record_count"] == len(mapped)
    assert bpa["unmapped_record_count"] == bpa["record_count"] - bpa["mapped_record_count"]
    assert float(bpa.get("threshold_mw", 0)) == 100.0
    assert all(r.get("capacity_claims") and float(r["capacity_claims"][0].get("value_mw", 0)) >= 100.0 for r in records)
    population = bpa.get("source", {}).get("source_population_accounting", {})
    assert int(population.get("eligible_rows_at_threshold_mw", -1)) == bpa["record_count"]
    assert int(population.get("raw_l_series_rows_on_record", -1)) >= bpa["record_count"]
    assert len(read_csv("data/bpa_large_load_registry.csv")) == bpa["record_count"]
    sha = bpa["source"].get("raw_official_snapshot_sha256")
    if sha:
        assert len(sha) == 64
        assert all(r.get("source_provenance", {}).get("workbook_sha256") == sha for r in records)
        assert all(r["map_provenance"].get("precision") == r.get("map_precision") for r in mapped)


def test_queue_snapshots_agree_with_their_status():
    status = {f["id"]: f for f in load("data/queue_layer_status.json")["feeds"]}
    for feed in status.values():
        snapshot = ROOT / feed["snapshot"]
        assert feed["snapshot_present"] == snapshot.exists(), f"{feed['id']}: snapshot_present is wrong"
        if not snapshot.exists():
            continue
        obj = json.loads(snapshot.read_text(encoding="utf-8"))
        assert obj["record_count"] == len(obj["records"]) == feed["record_count"] > 0, feed["id"]
    layers = {x["id"]: x for x in load("data/map_layer_manifest.json")["layers"]}
    if not status["NYISO"]["snapshot_present"]:
        assert layers["NYISO_COMPLETE_QUEUE"]["status"].startswith("snapshot not currently present")


def test_registry_shards_cover_the_registry():
    shard = load("data/facility_records/index.json")
    assert shard["record_count"] == len(registry_rows()) == sum(shard["rto_counts"].values())


def test_track3_ledgers_reconcile():
    n_sites = reference_universe_size()
    summary = load("data/track3/summary.json")
    assert summary["epoch_site_count"] == n_sites
    evidence = load("data/track3/evidence_records.json")
    assert evidence["record_count"] == len(evidence["records"]) == summary["track3_evidence_record_count"] > 0
    rs = load("data/track3/remote_sensing_observations.json")
    assert summary["remote_sensing_derived_observation_count"] == rs["derived_observation_count"] == len(rs["records"])
    assert summary["transformer_event_count"] == len(load("data/track3/transformer_supply_chain_events.json")["records"])
    enrich = load("data/track3/public_web_enrichment_2026-09-27.json")
    assert summary["public_web_evidence_record_count"] == enrich["record_count"] == len(enrich["records"])
    assert summary["public_web_evidence_site_count"] == enrich["accounting"]["sites_with_findings"] <= n_sites
    observation = load("data/track3/observation_queue.json")
    assert len(observation["tasks"]) == summary["observation_task_count"] == sum(summary["observation_task_counts_by_domain"].values())
    backlog = load("data/track3/research_backlog_summary.json")
    sweep = load("data/track3/site_missing_information_sweep_2026-09-27.json")["summary"]
    assert backlog["publisher_tasks"] == sweep["effective_unresolved_publisher_fields"]
    assert backlog["domain_tasks"] == sweep["open_track3_domain_cells"]
    assert backlog["total_tasks"] == backlog["publisher_tasks"] + backlog["domain_tasks"]
    assert backlog["sites"] == n_sites
    targets = load("data/track3/remote_sensing_observation_targets.json")
    physical = load("data/physical_verification_layer.json")["summary"]
    assert targets["record_count"] == len(targets["records"]) == n_sites
    assert targets["summary"]["derived_observation_count"] == physical["derived_observation_count"] > 0
    assert 0 < targets["summary"]["sites_with_any_derived_observation"] == physical["derived_observation_sites"] <= n_sites


def test_public_web_claims_mirror_their_source():
    source = load("data/track3/public_web_enrichment_2026-09-27.json")["records"]
    claims = load("data/track3/public_web_claims.json")["claims"]

    def key(x):
        return json.dumps({"site_name": x.get("site_name"), "field": x.get("field"), "value": x.get("value"),
                           "relationship": x.get("relationship"), "source": x.get("source"),
                           "source_urls": x.get("source_urls") or [], "publication_date": x.get("publication_date"),
                           "source_record_id": x.get("evidence_id") or x.get("source_record_id")},
                          sort_keys=True, ensure_ascii=False)

    assert len(source) == len(claims) == len({key(x) for x in source})
    assert {key(x) for x in source} == {key(x) for x in claims}
    assert len({x["claim_id"] for x in claims}) == len(claims)
    assert all(x.get("source_urls") for x in claims)
    assert all(x.get("epoch_id") for x in claims if x.get("claim_scope") == "site_level_public_web")
    assert all(x.get("claim_scope") in {"site_level_public_web", "state_or_multi_site_public_web"} for x in claims)


def test_public_research_leads():
    d = load("data/track3/public_research_leads.json")
    rows = d["records"]
    assert d["accounting"]["lead_count"] == len(rows) == len({x["lead_id"] for x in rows}) > 0
    assert d["accounting"]["site_count"] == len({x["epoch_id"] for x in rows})
    assert all(x["epoch_id"] and x["field"] and x["finding"] for x in rows)
    assert all(x["status"] in {"PUBLIC_LEAD_REVIEW_REQUIRED", "RETAINED_SOURCE", "PUBLIC_SOURCE"} for x in rows)


def test_closed_cases_and_strict_discovery():
    cases = load("data/track3/ambiguous_case_studies.json")["cases"]
    assert cases
    for case in cases:
        q = case["queue"]
        assert str(q["project_type"]).strip().lower() in {"load", "new load facility", "increase load"}
        assert q.get("classification_basis") and case.get("unresolved_items")
    strict = load("data/track3/strict_discovery_candidates.json")["candidates"]
    ids = [x["queue_id"] for x in strict]
    assert ids and len(ids) == len(set(ids))
    for x in strict:
        assert x["capacity_mw"] >= 100 and x["load_status"] == "PUBLICLY_CLASSIFIED_LOAD"
        assert x["identity_gap"] and x["physical_gap"]
    protocol = text("docs/CLOSED_CASE_PROTOCOL.md" if (ROOT / "docs/CLOSED_CASE_PROTOCOL.md").exists() else "CLOSED_CASE_PROTOCOL.md")
    assert "Candidate admission gate" in protocol and "Generation, surplus, transmission" in protocol


def test_catalog_lists_only_real_files():
    missing = [d["path"] for d in load("data/public_data_catalog.json")["datasets"] if not (ROOT / d["path"]).exists()]
    assert not missing, f"public_data_catalog.json lists missing files: {missing}"


# --------------------------------------------------------------------------- site


def test_homepage_project_counts_match_the_project_layer():
    html = text("index.html")
    n = load("data/project_level_extractions.json")["record_count"]
    shown = re.findall(r"Browse all (\d[\d,]*) extracted project-level records", html)
    shown += re.findall(r'placeholder="Search (\d[\d,]*) project records"', html)
    shown += re.findall(r'<p class="mono text-xl">(\d[\d,]*)</p><p[^>]*>Project-level records', html)
    assert shown, "homepage no longer shows the project-level count"
    assert {int(x.replace(",", "")) for x in shown} == {n}


def test_storage_rows_carry_no_compute_estimates():
    """Battery storage is not computational load; it must never show GPU or FLOP figures."""
    storage = [r for r in registry_rows() if str(r.get("tier", "")).startswith("Confirmed Grid-Scale Storage")]
    assert storage, "expected storage rows in the registry"
    offenders = [r["id"] if "id" in r else r.get("q") for r in storage if r.get("gpu") or r.get("flops") or r.get("flag")]
    assert not offenders, f"{len(offenders)} storage rows carry compute estimates, e.g. {offenders[:5]}"


def _inline_scripts(html: str) -> list[str]:
    blocks = []
    for attrs, body in re.findall(r"<script(?![^>]*\bsrc=)([^>]*)>(.*?)</script>", html, flags=re.S | re.I):
        kind = re.search(r'type\s*=\s*["\']([^"\']+)', attrs)
        if kind and kind.group(1).lower() not in {"text/javascript", "module"}:
            continue  # JSON / JSON-LD data blocks
        blocks.append(body)
    return blocks


@pytest.mark.skipif(shutil.which("node") is None, reason="node is required for the JavaScript syntax check")
@pytest.mark.parametrize("page", [p.name for p in pages()])
def test_inline_javascript_parses(page, tmp_path):
    for i, body in enumerate(_inline_scripts(text(page)), 1):
        js = tmp_path / f"block{i}.js"
        js.write_text(body, encoding="utf-8")
        proc = subprocess.run(["node", "--check", str(js)], capture_output=True, text=True)
        assert proc.returncode == 0, f"{page} script block {i}: {proc.stderr.strip()[:600]}"


@pytest.mark.parametrize("page", [p.name for p in pages()])
def test_local_links_resolve(page):
    html = text(page)
    broken = []
    for ref in re.findall(r'''(?:href|src)\s*=\s*["']([^"'#]+)["']''', html):
        ref = ref.strip()
        if re.match(r"^(https?:|mailto:|data:|javascript:|tel:|//)", ref) or "${" in ref or "+" in ref:
            continue
        if not (ROOT / ref.split("?")[0]).exists():
            broken.append(ref)
    assert not broken, f"{page}: broken local links {sorted(set(broken))}"


def test_robots_and_sitemap():
    assert f"Sitemap: {SITE}sitemap.xml" in text("robots.txt")
    urls = re.findall(r"<loc>(.*?)</loc>", text("sitemap.xml"))
    assert urls and all(u.startswith(SITE) for u in urls)
    for url in urls:
        rel = url[len(SITE):] or "index.html"
        assert (ROOT / rel).exists(), f"sitemap lists a page that does not exist: {url}"
    for page in ("index.html", "track3.html", "plan-a.html", "research.html", "api.html", "bulk-download.html"):
        assert f"{SITE}{'' if page == 'index.html' else page}" in urls
