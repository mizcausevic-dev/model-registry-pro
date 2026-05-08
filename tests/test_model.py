import pytest
from model_registry_pro import ModelVersion, Model, Stage, ApprovalState


def test_model_version_str():
    mv = ModelVersion(name="rag-agent", version="1.0.0")
    assert str(mv) == "rag-agent:1.0.0"


def test_model_version_parse():
    mv = ModelVersion.parse("rag-agent:1.2.3")
    assert mv.name == "rag-agent"
    assert mv.version == "1.2.3"


def test_model_version_parse_invalid():
    with pytest.raises(ValueError):
        ModelVersion.parse("just-a-name")


def test_model_version_validation():
    with pytest.raises(ValueError):
        ModelVersion(name="", version="1.0")
    with pytest.raises(ValueError):
        ModelVersion(name="bad name", version="1.0")
    with pytest.raises(ValueError):
        ModelVersion(name="bad/name", version="1.0")


def test_model_version_frozen():
    mv = ModelVersion(name="a", version="1.0")
    with pytest.raises(Exception):
        mv.name = "b"  # frozen dataclass


def test_model_with_metadata():
    mv = ModelVersion(name="search", version="2.0")
    m = Model(version=mv, description="search agent", metadata={"params": "1.5B"}, tags={"prod-ready"})
    assert m.metadata["params"] == "1.5B"
    assert "prod-ready" in m.tags


def test_stage_enum_values():
    assert Stage.DEV.value == "dev"
    assert Stage.PROD.value == "prod"


def test_approval_state_values():
    assert ApprovalState.PENDING.value == "pending"
