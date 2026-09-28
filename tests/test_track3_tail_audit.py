
from track3_tail_audit import *

def accounts():
    return {
        "A": OwnerAccount("A", 2, 2, 0, True),
        "B": OwnerAccount("B", 4, 0, 0, True),
    }

def test_weighted_sampling_is_reproducible():
    r=[TailRecipient("A",4),TailRecipient("B",6)]
    x=run_tail_population(r,accounts(),5,"seed")
    y=run_tail_population(r,accounts(),5,"seed")
    assert x["outcomes"]==y["outcomes"]

def test_balanced_population_produces_zero_failures():
    r=run_tail_population([TailRecipient("A",4),TailRecipient("B",6)],accounts(),5,"seed")
    assert r["failures"]==0
    assert r["upper_bound_untraced_tail_units"]>0

def test_incomplete_account_is_failure():
    bad={"A":OwnerAccount("A",2,2,0,False)}
    r=run_tail_population([TailRecipient("A",1)],bad,1,"seed")
    assert r["failures"]==1

def test_missing_owner_is_failure():
    r=run_tail_population([TailRecipient("MISSING",1)],{},1,"seed")
    assert r["failures"]==1
