
#!/usr/bin/env python3
"""Track 3 sampled-tail trace and account reconciliation model.

Implements the small-owner tail logic described in the AI 2040 covert-compute
verification scenario. It is a research model and requires a genuinely closed
sampling frame plus authoritative source records before any field certificate.
"""
from __future__ import annotations
import argparse, hashlib, json, math, random
from dataclasses import dataclass
from pathlib import Path

@dataclass(frozen=True)
class TailRecipient:
    owner_id: str
    delivered_units: int

@dataclass(frozen=True)
class OwnerAccount:
    owner_id: str
    current_holdings: int
    onward_sales: int
    documented_attrition: int
    independent_records_complete: bool

    def reconciles(self, received: int) -> bool:
        return (
            self.independent_records_complete
            and received == self.current_holdings + self.onward_sales + self.documented_attrition
        )

@dataclass(frozen=True)
class TraceOutcome:
    owner_id: str
    result: str
    reason: str

def seed_from_text(seed: str) -> int:
    return int(hashlib.sha256(seed.encode()).hexdigest()[:16], 16)

def sample_tail(recipient: TailRecipient, sample_size: int, seed: str) -> list[int]:
    if recipient.delivered_units <= 0:
        raise ValueError("delivered_units must be positive")
    if not 0 < sample_size <= recipient.delivered_units:
        raise ValueError("invalid sample_size")
    rng = random.Random(seed_from_text(seed))
    return rng.sample(range(recipient.delivered_units), sample_size)

def audit_recipient(recipient: TailRecipient, account: OwnerAccount) -> TraceOutcome:
    if not account.reconciles(recipient.delivered_units):
        return TraceOutcome(recipient.owner_id, "FAIL", "account does not reconcile or records are incomplete")
    if account.current_holdings > 0:
        return TraceOutcome(recipient.owner_id, "PASS", "sample can terminate at physically held inventory")
    if account.onward_sales > 0:
        return TraceOutcome(recipient.owner_id, "TRACE_FORWARD", "sample must continue through declared onward sales")
    return TraceOutcome(recipient.owner_id, "FAIL", "no physical holdings, onward sales, or valid endpoint")

def run_tail_population(
    recipients: list[TailRecipient],
    accounts: dict[str, OwnerAccount],
    sample_size: int,
    seed: str,
    delta: float = 0.05,
) -> dict:
    if not recipients:
        return {"status": "UNKNOWN", "reason": "empty sampling frame"}
    if not 0 < delta < 1:
        raise ValueError("delta must be in (0,1)")
    total_units = sum(r.delivered_units for r in recipients)
    if sample_size > total_units:
        raise ValueError("sample_size exceeds tail population")
    # Sample recipient proportional to delivered compute, then draw a unit
    # within that recipient. This matches the intended size-weighted tail logic.
    population = []
    for r in recipients:
        population.extend([r.owner_id] * r.delivered_units)
    rng = random.Random(seed_from_text(seed))
    chosen = rng.sample(range(len(population)), sample_size)
    outcomes = [audit_recipient(TailRecipient(owner, 1), accounts[owner]) if owner in accounts else TraceOutcome(owner,"FAIL","owner account unavailable") for owner in (population[i] for i in chosen)]
    failures = sum(o.result == "FAIL" for o in outcomes)
    if failures == 0:
        upper_failure_rate = 1 - delta ** (1.0 / sample_size)
        method = "exact_zero_failure_binomial_upper"
    else:
        # Use a conservative normal-approximation upper bound and label it as
        # such; callers requiring exact finite-population inference must replace
        # this with their preregistered design.
        phat = failures / sample_size
        z = 1.959963984540054
        se = math.sqrt(max(phat * (1-phat) / sample_size, 0.0))
        upper_failure_rate = min(1.0, phat + z*se)
        method = "conservative_normal_upper_nonzero_failures"
    return {
        "schema_version": 1,
        "status": "RESEARCH_MODEL_ONLY",
        "tail_population_units": total_units,
        "sample_size": sample_size,
        "seed": seed,
        "failures": failures,
        "passes": sample_size - failures,
        "upper_failure_rate": upper_failure_rate,
        "upper_bound_untraced_tail_units": total_units * upper_failure_rate,
        "delta": delta,
        "bound_method": method,
        "outcomes": [o.__dict__ for o in outcomes],
        "limitations": [
            "The result is conditional on a genuinely closed tail sampling frame.",
            "The example trace representation does not preserve individual serial-number identity through every resale.",
            "Nonzero-failure inference uses a deliberately labeled approximation rather than silently claiming an exact treaty-grade confidence interval.",
        ],
    }

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", type=Path, required=True)
    ap.add_argument("--sample-size", type=int, required=True)
    ap.add_argument("--seed", required=True)
    ap.add_argument("--delta", type=float, default=0.05)
    args = ap.parse_args()
    data = json.loads(args.input.read_text(encoding="utf-8"))
    recipients = [TailRecipient(**x) for x in data["recipients"]]
    accounts = {x["owner_id"]: OwnerAccount(**x) for x in data["accounts"]}
    print(json.dumps(run_tail_population(recipients, accounts, args.sample_size, args.seed, args.delta), indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
