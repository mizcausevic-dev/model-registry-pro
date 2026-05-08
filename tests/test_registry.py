import pytest
from model_registry_pro import (
    ModelRegistry, Model, ModelVersion, Stage,
    DuplicateModel, ModelNotFound, InvalidTransition,
)
from model_registry_pro.policy import OpenPolicy


def _model(name: str, version: str, parent=None) -> Model:
    return Model(version=ModelVersion(name=name, version=version), parent=parent)


def test_register_and_get():
    r = ModelRegistry(policy=OpenPolicy())
    m = _model("rag", "1.0.0")
    r.register(m)
    assert r.get(ModelVersion("rag", "1.0.0")) is m


def test_register_duplicate_rejected():
    r = ModelRegistry(policy=OpenPolicy())
    r.register(_model("rag", "1.0.0"))
    with pytest.raises(DuplicateModel):
        r.register(_model("rag", "1.0.0"))


def test_register_with_unknown_parent_rejected():
    r = ModelRegistry(policy=OpenPolicy())
    with pytest.raises(ModelNotFound):
        r.register(Model(
            version=ModelVersion("derived", "1.0"),
            parent=ModelVersion("ghost", "0.1"),
        ))


def test_get_unknown_raises():
    r = ModelRegistry(policy=OpenPolicy())
    with pytest.raises(ModelNotFound):
        r.get(ModelVersion("ghost", "1.0"))


def test_default_stage_is_dev():
    r = ModelRegistry(policy=OpenPolicy())
    r.register(_model("rag", "1.0"))
    assert r.stage_of(ModelVersion("rag", "1.0")) == Stage.DEV


def test_list_versions():
    r = ModelRegistry(policy=OpenPolicy())
    r.register(_model("rag", "1.0"))
    r.register(_model("rag", "1.1"))
    r.register(_model("search", "2.0"))
    rag_versions = r.list_versions("rag")
    assert len(rag_versions) == 2
    assert all(m.version.name == "rag" for m in rag_versions)


def test_invalid_transition_rejected():
    r = ModelRegistry(policy=OpenPolicy())
    r.register(_model("rag", "1.0"))
    # Cannot go DEV -> PROD directly (must go through STAGING)
    with pytest.raises(InvalidTransition):
        r.request_promotion(ModelVersion("rag", "1.0"), Stage.PROD, requested_by="alice")


def test_production_version_returns_only_prod():
    r = ModelRegistry(policy=OpenPolicy())
    r.register(_model("rag", "1.0"))
    r.register(_model("rag", "2.0"))
    # Promote 2.0 to prod via DEV -> STAGING -> PROD
    v2 = ModelVersion("rag", "2.0")
    r.request_promotion(v2, Stage.STAGING, requested_by="alice")
    r.request_promotion(v2, Stage.PROD, requested_by="alice")
    prod = r.production_version("rag")
    assert prod is not None and str(prod.version) == "rag:2.0"


def test_by_stage_filters():
    r = ModelRegistry(policy=OpenPolicy())
    r.register(_model("a", "1.0"))
    r.register(_model("b", "1.0"))
    r.request_promotion(ModelVersion("a", "1.0"), Stage.STAGING, requested_by="x")
    dev_models = r.by_stage(Stage.DEV)
    staging_models = r.by_stage(Stage.STAGING)
    assert len(dev_models) == 1
    assert len(staging_models) == 1
    assert staging_models[0].version.name == "a"
