from model_registry_pro import DefaultPolicy
from model_registry_pro.model import Stage, ModelVersion
from model_registry_pro.policy import OpenPolicy


_MV = ModelVersion("test", "1.0")


def test_default_policy_dev_to_staging_no_approval():
    p = DefaultPolicy()
    assert p.requires_approval(_MV, Stage.DEV, Stage.STAGING) is False


def test_default_policy_staging_to_prod_requires_approval():
    p = DefaultPolicy()
    assert p.requires_approval(_MV, Stage.STAGING, Stage.PROD) is True


def test_default_policy_approver_allowlist():
    p = DefaultPolicy(approvers={"alice", "bob"})
    assert p.can_approve("alice", _MV, Stage.PROD) is True
    assert p.can_approve("eve", _MV, Stage.PROD) is False


def test_default_policy_empty_approvers_allows_anyone():
    p = DefaultPolicy(approvers=set())
    assert p.can_approve("anyone", _MV, Stage.PROD) is True


def test_default_policy_empty_approver_string_denied():
    p = DefaultPolicy()
    assert p.can_approve("", _MV, Stage.PROD) is False


def test_open_policy_allows_everything():
    p = OpenPolicy()
    assert p.requires_approval(_MV, Stage.STAGING, Stage.PROD) is False
    assert p.can_approve("anyone", _MV, Stage.PROD) is True
