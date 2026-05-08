"""model-registry-pro: model lifecycle catalog with lineage, approval gates, and stage promotion."""
from .model import Model, ModelVersion, Stage, ApprovalState, Approval
from .exceptions import (
    ModelNotFound, DuplicateModel, InvalidTransition,
    ApprovalNotFound, PolicyDenied,
)
from .policy import PromotionPolicy, DefaultPolicy
from .lineage import LineageGraph
from .registry import ModelRegistry

__version__ = "0.1.0"
__all__ = [
    "Model", "ModelVersion", "Stage", "ApprovalState", "Approval",
    "ModelNotFound", "DuplicateModel", "InvalidTransition",
    "ApprovalNotFound", "PolicyDenied",
    "PromotionPolicy", "DefaultPolicy",
    "LineageGraph", "ModelRegistry",
]
