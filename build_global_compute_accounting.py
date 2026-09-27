#!/usr/bin/env python3
"""Build the global public-source compute-accounting evidence summary."""

from __future__ import annotations
import csv
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parent
EXT=ROOT/"data/external/epoch_ai"

FILES={
 "owners":EXT/"ai_chip_owners_cumulative_by_designer.csv",
 "users":EXT/"ai_chip_users_year_end_by_lab.csv",
 "sales_orgs":EXT/"ai_chip_sales_organizations.csv",
 "sales_types":EXT/"ai_chip_sales_chip_types.csv",
 "sales_timeline":EXT/"ai_chip_sales_timelines_by_chip.csv",
 "components_chip":EXT/"ai_chip_components_quarterly_by_chip.csv",
 "components_designer":EXT/"ai_chip_components_quarterly_by_designer.csv",
 "supply":EXT/"ai_chip_components_supply_denominators.csv",
}

def rows(path: Path):
    with path.open("r",encoding="utf-8",newline="") as f:
        return list(csv.DictReader(f))

def uniq(xs): return sorted({x for x in xs if x})

def main():
    data={k:rows(v) for k,v in FILES.items()}
    sales_timeline=data["sales_timeline"]
    out={
      "schema_version":1,
      "generated_on":"2026-09-27",
      "title":"Global AI-compute supply-chain evidence layer",
      "current":{
        "owner_cumulative_rows":len(data["owners"]),
        "distinct_owners":len(uniq([r.get("Owner","") for r in data["owners"]])),
        "distinct_chip_manufacturers":len(uniq([r.get("Chip manufacturer","") for r in data["owners"]])),
        "user_year_end_rows":len(data["users"]),
        "distinct_labs":len(uniq([r.get("Lab","") for r in data["users"]])),
        "sales_organization_rows":len(data["sales_orgs"]),
        "sales_chip_type_rows":len(data["sales_types"]),
        "sales_timeline_rows":len(sales_timeline),
        "distinct_chip_types":len(uniq([r.get("Chip type","") for r in sales_timeline])),
        "component_by_chip_rows":len(data["components_chip"]),
        "component_by_designer_rows":len(data["components_designer"]),
        "supply_denominator_rows":len(data["supply"]),
        "global_transaction_level_closure":"UNKNOWN",
        "current_untraced_pool":"UNKNOWN"
      },
      "source_files":{
        "owners":"data/external/epoch_ai/ai_chip_owners_cumulative_by_designer.csv",
        "users":"data/external/epoch_ai/ai_chip_users_year_end_by_lab.csv",
        "sales_organizations":"data/external/epoch_ai/ai_chip_sales_organizations.csv",
        "sales_chip_types":"data/external/epoch_ai/ai_chip_sales_chip_types.csv",
        "sales_timeline":"data/external/epoch_ai/ai_chip_sales_timelines_by_chip.csv",
        "components_by_chip":"data/external/epoch_ai/ai_chip_components_quarterly_by_chip.csv",
        "components_by_designer":"data/external/epoch_ai/ai_chip_components_quarterly_by_designer.csv",
        "supply_denominators":"data/external/epoch_ai/ai_chip_components_supply_denominators.csv"
      },
      "reconciliation_rules":[
        "Cumulative owner snapshots overlap in time and cannot be summed into inventory.",
        "Sales estimates cannot be treated as serial-numbered shipment records.",
        "Organization-level ownership does not establish physical end use.",
        "Component supply denominators constrain plausibility but do not identify exact accelerator units.",
        "Residual compute remains UNKNOWN until the transaction/inspection chain is closed."
      ]
    }
    path=ROOT/"data/track3/global_compute_supply_chain.json"
    path.write_text(json.dumps(out,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print("WROTE",path)
    return 0

if __name__=="__main__":
    raise SystemExit(main())
