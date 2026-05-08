import pytest
from model_registry_pro import (
    ModelRegistry, Model, ModelVersion, Stage, ApprovalState,
    DefaultPolicy, ApprovalNotFound, PolicyDenied, InvalidTransition,
)
from model_registry_pro.policy import OpenPolicy


def _setup() -> tuple[ModelRegistry, ModelVersion]:
    r = ModelRegistry(policy=DefaultPolicy(approvers={"alice", "bob"}))
    m = Model(version=ModelVersion("rag", "1.0"))
    r.register(m)
    return r, m.version


def test_dev_to_staging_no_approval():
    """Default policy: DEV -> STAGING is auto-approved (no human gate)."""
    r, mv = _setup()
    approval = r.request_promotion(mv, Stage.STAGING, requested_by="dev1")
    assert approval.state == ApprovalState.APPROVED
    assert r.stage_of(mv) == Stage.STAGING


def test_staging_to_prod_requires_approval():
    r, mv = _setup()
    r.request_promotion(mv, Stage.STAGING, requested_by="dev1")
    approval = r.request_promotion(mv, Stage.PROD, requested_by="dev1")
    assert approval.state == ApprovalState.PENDING
    assert r.stage_of(mv) == Stage.STAGING  # Stage NOT yet changed


def test_approve_advances_stage():
    r, mv = _setup()
    r.request_promotion(mv, Stage.STAGING, requested_by="dev1")
    pending = r.request_promotion(mv, Stage.PROD, requested_by="dev1")
    r.approve(pending.id, approved_by="alice", notes="LGTM")
    assert r.stage_of(mv) == Stage.PROD
    assert pending.state == ApprovalState.APPROVED


def test_reject_keeps_stage():
    r, mv = _setup()
    r.request_promotion(mv, Stage.STAGING, requested_by="dev1")
    pending = r.request_promotion(mv, Stage.PROD, requested_by="dev1")
    r.reject(pending.id, decided_by="alice", notes="latency regression")
    assert pending.state == ApprovalState.REJECTED
    assert r.stage_of(mv) == Stage.STAGING


def test_unknown_approver_denied():
    r, mv = _setup()
    r.request_promotion(mv, Stage.STAGING, requested_by="dev1")
    pending = r.request_promotion(mv, Stage.PROD, requested_by="dev1")
    with pytest.raises(PolicyDenied):
        r.approve(pending.id, approved_by="random-user")


def test_distinct_approver_required():
    r, mv = _setup()
    r.request_promotion(mv, Stage.STAGING, requested_by="alice")
    pending = r.request_promotion(mv, Stage.PROD, requested_by="alice")
    with pytest.raises(PolicyDenied):
        r.approve(pending.id, approved_by="alice")


def test_double_decision_rejected():
    r, mv = _setup()
    r.request_promotion(mv, Stage.STAGING, requested_by="dev1")
    pending = r.request_promotion(mv, Stage.PROD, requested_by="dev1")
    r.approve(pending.id, approved_by="alice")
    with pytest.raises(InvalidTransition):
        r.approve(pending.id, approved_by="bob")


def test_approval_not_found():
    r, _ = _setup()
    with pytest.raises(ApprovalNotFound):
        r.approve(9999, approved_by="alice")


def test_pending_approvals_listing():
    r = ModelRegistry(policy=DefaultPolicy(approvers={"alice"}))
    a = Model(version=ModelVersion("a", "1.0"))
    b = Model(version=ModelVersion("b", "1.0"))
    r.register(a)
    r.register(b)
    r.request_promotion(a.version, Stage.STAGING, requested_by="dev")
    r.request_promotion(b.version, Stage.STAGING, requested_by="dev")
    p1 = r.request_promotion(a.version, Stage.PROD, requested_by="dev")
    p2 = r.request_promotion(b.version, Stage.PROD, requested_by="dev")
    pending = r.pending_approvals()
    assert len(pending) == 2
    assert {p.id for p in pending} == {p1.id, p2.id}


def test_approval_history():
    r, mv = _setup()
    r.request_promotion(mv, Stage.STAGING, requested_by="dev1")
    pending = r.request_promotion(mv, Stage.PROD, requested_by="dev1")
    r.approve(pending.id, approved_by="alice")
    history = r.approval_history(mv)
    assert len(history) == 2
    assert all(a.state == ApprovalState.APPROVED for a in history)
