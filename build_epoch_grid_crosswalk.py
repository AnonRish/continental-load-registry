#!/usr/bin/env python3
"""Build the geographic queue/connection crosswalk for every imported Epoch AI site.

This layer answers two different questions without conflating them:
1. Which grid/interconnection jurisdiction should contain the site's record?
2. Do we have a defensible site-specific public queue/service record?

A jurisdiction mapping is not a site-specific queue ID.
"""

from __future__ import annotations
import csv, json, re, sys
from pathlib import Path
from datetime import date
from typing import Any

ROOT = Path(__file__).resolve().parent
EPOCH = ROOT / "data" / "external" / "epoch_ai"
CENTERS = EPOCH / "data_centers.csv"
REGISTRY = EPOCH / "registry.json"
OUT_CSV = EPOCH / "queue_crosswalk.csv"
OUT_JSON = EPOCH / "queue_crosswalk.json"

STATE_BY_SITE = {
    # Tennessee
    "Colossus 1":"TN","Colossus 2":"TN","Meta Gallatin":"TN",
    # Georgia
    "Microsoft Fairwater Atlanta":"GA","CoreWeave Dalton 1 & 2":"GA","xAI QTS Atlanta":"GA",
    # Indiana
    "Anthropic-Amazon New Carlisle":"IN","Meta Jeffersonville":"IN","Google Fort Wayne":"IN",
    # Oklahoma
    "Google Pryor (North)":"OK","CoreWeave Muskogee OK":"OK",
    # Ohio
    "Meta Prometheus":"OH","Google Columbus":"OH","Google New Albany":"OH","AWS New Albany":"OH","Google Lancaster":"OH",
    "Meta Bowling Green":"OH","OpenAI Stargate Lordstown":"OH",
    # Texas
    "OpenAI Stargate Abilene":"TX","CoreWeave Denton TX":"TX","Meta Temple":"TX","Coreweave Helios":"TX","Anthropic Barber Lake":"TX",
    "Google Midlothian":"TX","Google Red Oak":"TX","Microsoft SAT40":"TX","Microsoft SAT14":"TX",
    "Vantage TX1":"TX","Crusoe Abilene Expansion":"TX","Goodnight":"TX","OpenAI Stargate Shackelford":"TX",
    # Wisconsin
    "Microsoft Fairwater Wisconsin":"WI","OpenAI Stargate Wisconsin":"WI",
    # Iowa
    "Google Council Bluffs (East)":"IA","Microsoft Project Osmium":"IA","Google Cedar Rapids":"IA","QTS Cedar Rapids":"IA",
    # Virginia
    "QTS Richmond 1":"VA","Google Bristow":"VA","QTS Richmond 2":"VA","QTS Richmond 3":"VA",
    "Google Arcola":"VA","CoreWeave Chester VA":"VA","STACK Infrastructure NVA02":"VA",
    # Minnesota
    "Meta Rosemount":"MN",
    # Arizona
    "Google Mesa":"AZ","Microsoft Goodyear":"AZ","Stream Phoenix":"AZ",
    # Nebraska
    "Google Omaha":"NE","Google Lincoln":"NE","Google Papillion":"NE","Meta Sarpy":"NE",
    # Alabama
    "Meta Montgomery":"AL","Meta Huntsville":"AL",
    # Wyoming
    "Meta Cheyenne":"WY",
    # Utah
    "Meta Eagle Mountain":"UT","QTS Eagle Mountain":"UT",
    # New Mexico
    "Meta Los Lunas":"NM","OpenAI Stargate New Mexico":"NM",
    # North Dakota
    "CoreWeave Ellendale ND":"ND",
    # Pennsylvania
    "AWS Berwick":"PA","CoreWeave Lancaster Greenfield site":"PA",
    # North Carolina
    "CoreWeave Marble NC":"NC",
    # South Carolina
    "Meta Aiken":"SC",
    # Louisiana
    "Meta Hyperion":"LA",
    # New York
    "Core42 Lake Mariner":"NY","Anthropic Lake Mariner":"NY",
    # Missouri
    "Google Kansas City East":"MO",
    # Nevada
    "Google Storey County":"NV",
    # Idaho
    "Meta Kuna":"ID",
    # Mississippi
    "Amazon Madison Mega Site":"MS","Amazon Ridgeland":"MS",
    # New Jersey
    "Microsoft-Nebius New Jersey":"NJ",
    # Michigan
    "OpenAI Stargate Michigan":"MI",
    # Oregon
    "Google The Dalles":"OR","Meta-QTS Hillsboro 2":"OR",
}

RTO = {
    "TX": ("ERCOT", "RTO/ISO official", "https://www.ercot.com/services/rq/large-load-integration"),
    "NY": ("NYISO", "RTO/ISO official", "https://www.nyiso.com/documents/20142/1407078/NYISO-Interconnection-Queue.xlsx"),
    "WI": ("MISO", "RTO/ISO official", "https://www.misoenergy.org/api/giqueue/getprojects"),
    "IA": ("MISO", "RTO/ISO official", "https://www.misoenergy.org/api/giqueue/getprojects"),
    "IN": ("MISO", "RTO/ISO official", "https://www.misoenergy.org/api/giqueue/getprojects"),
    "MN": ("MISO", "RTO/ISO official", "https://www.misoenergy.org/api/giqueue/getprojects"),
    "MI": ("MISO", "RTO/ISO official", "https://www.misoenergy.org/api/giqueue/getprojects"),
    "ND": ("MISO", "RTO/ISO official", "https://www.misoenergy.org/api/giqueue/getprojects"),
    "LA": ("MISO", "RTO/ISO official", "https://www.misoenergy.org/api/giqueue/getprojects"),
    "MS": ("MISO", "RTO/ISO official", "https://www.misoenergy.org/api/giqueue/getprojects"),
    "OH": ("PJM", "RTO/ISO official", "https://www.pjm.com/planning/service-requests"),
    "VA": ("PJM", "RTO/ISO official", "https://www.pjm.com/planning/service-requests"),
    "NJ": ("PJM", "RTO/ISO official", "https://www.pjm.com/planning/service-requests"),
    "PA": ("PJM", "RTO/ISO official", "https://www.pjm.com/planning/service-requests"),
    "NE": ("SPP", "RTO/ISO official", "https://opsportal.spp.org/Studies/GIActive"),
    "OK": ("SPP", "RTO/ISO official", "https://opsportal.spp.org/Studies/GIActive"),
    "MO": ("SPP", "RTO/ISO official", "https://opsportal.spp.org/Studies/GIActive"),
}

NON_RTO = {
    "TN": ("TVA / Tennessee transmission providers", "state queue coverage index", "https://wattstreet.net/state/tn/"),
    "GA": ("SERC / Georgia transmission providers", "state queue coverage index", "https://wattstreet.net/state/ga/"),
    "AL": ("SERC / Alabama transmission providers", "state queue coverage index", "https://wattstreet.net/state/al/"),
    "NC": ("SERC / North Carolina transmission providers", "state queue coverage index", "https://wattstreet.net/state/nc/"),
    "SC": ("SERC / South Carolina transmission providers", "state queue coverage index", "https://wattstreet.net/state/sc/"),
    "AZ": ("WECC / Arizona serving utilities (APS / SRP)", "state queue coverage index", "https://wattstreet.net/state/az/"),
    "ID": ("WECC / Idaho Power, PacifiCorp, BPA and Avista", "state queue coverage index", "https://wattstreet.net/state/id/"),
    "NV": ("WECC / Nevada serving utility", "state queue coverage index", "https://wattstreet.net/state/nv/"),
    "UT": ("WECC / Utah serving utility", "state queue coverage index", "https://wattstreet.net/state/ut/"),
    "NM": ("WECC / PNM and other New Mexico serving utilities", "state queue coverage index", "https://wattstreet.net/state/nm/"),
    "WY": ("WECC / Wyoming serving utilities", "state queue coverage index", "https://wattstreet.net/state/wy/"),
    "OR": ("WECC / BPA and Pacific Northwest utilities", "state queue coverage index", "https://wattstreet.net/state/or/"),
}

INTERNATIONAL = {
    "Malaysia": ("Malaysia national / utility grid connection process", "country-level connection system"),
    "United Kingdom": ("Great Britain NESO + local distribution network connections", "national connection queue / contracted connections"),
    "China": ("China State Grid / provincial grid connection process", "national / provincial connection system"),
    "Indonesia": ("PLN grid connection process", "national utility connection system"),
    "Norway": ("Statnett + local distribution network connections", "national / local connection system"),
    "Finland": ("Fingrid + local distribution network connections", "national / local connection system"),
    "Australia": ("AEMO + local network service provider connections", "national market / NSP connection system"),
    "Portugal": ("REN + local network connection process", "transmission / distribution connection system"),
    "Iceland": ("Landsnet + local distribution network connections", "transmission / distribution connection system"),
    "Sweden": ("Svenska kraftnät + local distribution network connections", "national / local connection system"),
    "United Arab Emirates": ("UAE transmission / local distribution connection process", "utility connection system"),
}

SITE_SPECIFIC = {
    "Anthropic Lake Mariner": {
        "record_status":"site_specific_queue_verified","queue_id":"1670","queue_name":"Lake Mariner Data II",
        "queue_capacity_mw":250,"evidence_type":"NYISO Load Projects queue",
        "evidence_url":"https://www.nyiso.com/documents/20142/1407078/NYISO-Interconnection-Queue.xlsx",
        "basis":"NYISO Q1670 Lake Mariner Data II in Niagara County; campus identity aligns with Epoch's Barker site."
    },
    "Core42 Lake Mariner": {
        "record_status":"site_specific_queue_verified","queue_id":"1670","queue_name":"Lake Mariner Data II",
        "queue_capacity_mw":250,"evidence_type":"NYISO Load Projects queue",
        "evidence_url":"https://www.nyiso.com/documents/20142/1407078/NYISO-Interconnection-Queue.xlsx",
        "basis":"Same Lake Mariner campus as the Epoch Core42 record; queue is a request/phase and is not a 1:1 duplicate of Epoch IT power."
    },
    "CoreWeave Muskogee OK": {
        "record_status":"public_service_contract_verified","queue_name":"OG&E electric service agreement",
        "queue_capacity_mw":100,"evidence_type":"SEC-filed electric service agreement",
        "evidence_url":"https://investors.corescientific.com/sec-filings/all-sec-filings/content/0001193125-26-165121/d149019dex992.htm",
        "basis":"Public filing states power is supplied under an OG&E electric service agreement with estimated maximum demand of 100,000 kW for the Muskogee campus."
    },
    "OpenAI Stargate Michigan": {
        "record_status":"public_service_contract_verified","queue_name":"DTE special-contract / Stargate Michigan",
        "queue_capacity_mw":1383,"evidence_type":"Michigan Public Service Commission special-contract approval",
        "evidence_url":"https://www.michigan.gov/som/data-centers",
        "basis":"Michigan's official data-center page identifies MPSC approval of DTE Electric energy contracts; Epoch's site record cites the approval reporting 1,383 MW site capacity."
    },
    "Google Papillion": {
        "record_status":"public_customer_planning_record","queue_name":"OPPD Google Papillion large-customer planning",
        "queue_capacity_mw":None,"evidence_type":"OPPD public planning document",
        "evidence_url":"https://www.oppd.com/media/316613/neomaha01a-pos-2019.pdf",
        "basis":"OPPD public planning material discusses transmission/distribution improvements, capacity purchases and new generation to meet Google's expected system demand for the Papillion data center."
    },
}

def read_centers():
    with CENTERS.open("r",encoding="utf-8-sig",newline="") as f:
        return list(csv.DictReader(f))

def main():
    centers=read_centers()
    assert len(centers)==93, f"expected 93 Epoch sites, got {len(centers)}"
    records=[]
    for row in centers:
        name=row["Name"]
        country=row.get("Country","")
        address=row.get("Address","")
        site=SITE_SPECIFIC.get(name,{})
        if country=="United States":
            st=STATE_BY_SITE.get(name)
            if not st:
                raise RuntimeError(f"missing U.S. state mapping for {name!r}")
            if st in RTO:
                queue_system,source_type,source_url=RTO[st]
            else:
                queue_system,source_type,source_url=NON_RTO[st]
            status=site.get("record_status","queue_jurisdiction_mapped_site_id_not_yet_verified")
            rec={
                "epoch_name":name,"epoch_country":country,"epoch_address":address,"state_province":st,
                "queue_or_connection_system":queue_system,"queue_scope_status":"within_registry_geography",
                "site_record_status":status,"site_specific_queue_id":site.get("queue_id"),
                "site_specific_queue_name":site.get("queue_name"),"site_specific_queue_capacity_mw":site.get("queue_capacity_mw"),
                "source_type":site.get("evidence_type",source_type),
                "source_url":site.get("evidence_url",source_url),"source_date":"2026-09-26",
                "match_basis":site.get("basis",f"State {st} is assigned to the {queue_system} queue/connection jurisdiction; this establishes coverage, not a site-specific queue ID."),
                "confidence":"high" if site else "jurisdiction"
            }
        else:
            queue_system,source_type=INTERNATIONAL.get(country,(f"{country} grid connection process","country-level connection system"))
            status="outside_current_registry_geography"
            rec={
                "epoch_name":name,"epoch_country":country,"epoch_address":address,"state_province":"",
                "queue_or_connection_system":queue_system,"queue_scope_status":"outside_registry_geography",
                "site_record_status":"country_connection_system_mapped","site_specific_queue_id":None,
                "site_specific_queue_name":None,"site_specific_queue_capacity_mw":None,
                "source_type":source_type,"source_url":None,"source_date":"2026-09-26",
                "match_basis":"Epoch site is outside the current U.S./Canada nine-market registry geography; a national/utility connection system is recorded as the relevant external jurisdiction.",
                "confidence":"jurisdiction"
            }
        records.append(rec)

    with OUT_CSV.open("w",encoding="utf-8",newline="") as f:
        fields=list(records[0])
        w=csv.DictWriter(f,fieldnames=fields)
        w.writeheader(); w.writerows(records)

    reg=json.loads(REGISTRY.read_text(encoding="utf-8"))
    by_name={r["epoch_name"]:r for r in records}
    for rec in reg["records"]:
        name=rec["normalized"]["name"]
        g=by_name[name]
        rec["grid_crosswalk"]={
            "state_province":g["state_province"],
            "queue_or_connection_system":g["queue_or_connection_system"],
            "queue_scope_status":g["queue_scope_status"],
            "site_record_status":g["site_record_status"],
            "site_specific_queue_id":g["site_specific_queue_id"],
            "site_specific_queue_name":g["site_specific_queue_name"],
            "site_specific_queue_capacity_mw":g["site_specific_queue_capacity_mw"],
            "source_type":g["source_type"],
            "source_url":g["source_url"],
            "source_date":g["source_date"],
            "match_basis":g["match_basis"],
            "confidence":g["confidence"],
        }
    reg["grid_crosswalk_summary"]={
        "all_epoch_sites_have_jurisdiction":True,
        "sites_with_site_specific_queue_id":sum(1 for r in records if r["site_specific_queue_id"]),
        "sites_with_public_service_or_planning_record":sum(1 for r in records if r["site_record_status"] in {"public_service_contract_verified","public_customer_planning_record"}),
        "sites_with_queue_jurisdiction_only":sum(1 for r in records if r["site_record_status"]=="queue_jurisdiction_mapped_site_id_not_yet_verified"),
        "sites_outside_current_registry_geography":sum(1 for r in records if r["queue_scope_status"]=="outside_registry_geography"),
        "as_of":"2026-09-26"
    }
    REGISTRY.write_text(json.dumps(reg,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")

    payload={
        "schema_version":1,
        "generated_on":"2026-09-26",
        "record_count":len(records),
        "geographic_scope":"Epoch AI's imported 93-site dataset is global; the current queue registry is North American and based on nine U.S./Canada organized markets. This crosswalk adds a queue/connection jurisdiction for every Epoch site and preserves site-specific IDs only when defensible.",
        "records":records
    }
    OUT_JSON.write_text(json.dumps(payload,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print("built",len(records),"Epoch grid/queue jurisdiction records")
    print("site-specific IDs:",sum(1 for r in records if r["site_specific_queue_id"]))
    print("service/planning records:",sum(1 for r in records if r["site_record_status"] in {"public_service_contract_verified","public_customer_planning_record"}))
    print("jurisdiction-only:",sum(1 for r in records if r["site_record_status"]=="queue_jurisdiction_mapped_site_id_not_yet_verified"))
    print("outside registry geography:",sum(1 for r in records if r["queue_scope_status"]=="outside_registry_geography"))

if __name__=="__main__":
    main()
