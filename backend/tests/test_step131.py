import pytest
from backend.app.reality.confidence_signal_aggregator import RealityConfidenceSignalAggregator
from backend.app.reality.confidence_signals import RealityConfidenceSignalResult


def base():
    return ({"status":"usable"},{"status":"usable","claim_count":2,"linked_claim_count":2},{"status":"usable","stale_count":0,"unknown_count":0},{"status":"empty","conflict_count":0})


def test_full_grounding_signals_are_supported():
    r=RealityConfidenceSignalAggregator().aggregate_result(*base())
    assert r.status=="supported" and r.claim_coverage==1


def test_partial_linking_is_uncertain():
    e,l,f,c=base(); l={**l,"linked_claim_count":1}
    r=RealityConfidenceSignalAggregator().aggregate_result(e,l,f,c)
    assert r.status=="uncertain" and "partial_claim_evidence_coverage" in r.signals


def test_stale_sources_are_uncertain():
    e,l,f,c=base(); f={**f,"stale_count":1}
    r=RealityConfidenceSignalAggregator().aggregate_result(e,l,f,c)
    assert r.status=="uncertain" and "stale_sources_present" in r.signals


def test_conflicts_are_uncertain_not_suppressed():
    e,l,f,c=base(); c={"status":"usable","conflict_count":1}
    r=RealityConfidenceSignalAggregator().aggregate_result(e,l,f,c)
    assert r.status=="uncertain" and r.conflict_count==1


def test_missing_freshness_or_claims_is_uncertain():
    e,l,f,c=base(); f={"status":"unavailable"}
    assert RealityConfidenceSignalAggregator().aggregate_result(e,l,f,c).status=="uncertain"
    e,l,f,c=base(); l={"status":"empty","claim_count":0,"linked_claim_count":0}
    assert RealityConfidenceSignalAggregator().aggregate_result(e,l,f,c).status=="uncertain"


def test_insufficient_evidence_is_not_supported():
    r=RealityConfidenceSignalAggregator().aggregate_result({"status":"insufficient"},{"status":"empty","claim_count":0,"linked_claim_count":0},{"status":"unavailable"},{"status":"empty","conflict_count":0})
    assert r.status=="insufficient" and not r.evidence_usable


def test_contract_is_immutable_and_validates():
    r=RealityConfidenceSignalResult("supported",True,1.0,"usable",0,("ok",))
    assert r.to_dict()["claim_coverage"]==1.0
    with pytest.raises(Exception): r.status="x"
    with pytest.raises(ValueError): RealityConfidenceSignalResult("supported",True,1.5,"usable",0)
