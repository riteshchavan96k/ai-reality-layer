import pytest
from backend.app.reality.reality_state import RealityState
from backend.app.reality.reality_state_builder import RealityStateBuilder

def parts():
    return ({"status":"usable"},{"status":"usable","claim_count":1},{"status":"usable","claim_count":1,"linked_claim_count":1},{"status":"usable","source_count":1},{"status":"usable","source_count":1},{"status":"usable","source_count":1,"fresh_count":1,"stale_count":0,"unknown_count":0},{"status":"empty","conflict_count":0},{"status":"supported","evidence_usable":True,"claim_coverage":1.0})

def test_builder_assembles_all_existing_signals():
    r=RealityStateBuilder().build_result("test task",*parts())
    assert r.status=="supported" and r.claims["claim_count"]==1 and r.confidence_signals["claim_coverage"]==1.0

def test_serialization_shape():
    r=RealityStateBuilder().build("test task",*parts())
    assert list(r)==["status","task","evidence","claims","claim_evidence_linking","source_provenance","source_observation","freshness","conflicts","confidence_signals","assembly_method","reason"]

def test_confidence_state_drives_reality_state():
    p=list(parts()); p[-1]={"status":"uncertain","evidence_usable":True,"claim_coverage":0.5}
    assert RealityStateBuilder().build_result("task",*p).status=="uncertain"

def test_unavailable_requires_reason():
    p=list(parts()); p[-1]={"status":"unavailable","reason":"signals unavailable"}
    r=RealityStateBuilder().build_result("task",*p)
    assert r.status=="unavailable" and r.reason=="signals unavailable"

def test_invalid_inputs_fail_closed():
    with pytest.raises(ValueError): RealityStateBuilder().build_result("task",*parts()[:-1],{"status":"invalid"})
    with pytest.raises(ValueError): RealityStateBuilder().build_result("",*parts())

def test_contract_is_immutable():
    r=RealityStateBuilder().build_result("task",*parts())
    with pytest.raises(Exception): r.status="uncertain"
