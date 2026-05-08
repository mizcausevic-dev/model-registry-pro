"""Core domain types: Model, version, stages, approvals."""
from __future__ import annotations
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Optional, Set


@dataclass(frozen=True)
class ModelVersion:
    """Identifies a unique model release: name + semver-ish version string."""
    name: str
    version: str

    def __post_init__(self) -> None:
        if not self.name or not self.version:
            raise ValueError("ModelVersion requires both name and version")
        if "/" in self.name or " " in self.name:
            raise ValueError(f"Invalid model name: {self.name!r}")

    def __str__(self) -> str:
        return f"{self.name}:{self.version}"

    @classmethod
    def parse(cls, s: str) -> "ModelVersion":
        if ":" not in s:
            raise ValueError(f"Expected 'name:version', got: {s!r}")
        name, _, version = s.partition(":")
        return cls(name=name, version=version)


class Stage(str, Enum):
    """Lifecycle stage of a model version."""
    DEV = "dev"
    STAGING = "staging"
    PROD = "prod"
    DEPRECATED = "deprecated"
    RETIRED = "retired"


# Allowed forward transitions. Other moves require explicit override.
VALID_TRANSITIONS: Dict[Stage, Set[Stage]] = {
    Stage.DEV: {Stage.STAGING, Stage.RETIRED},
    Stage.STAGING: {Stage.PROD, Stage.DEV, Stage.RETIRED},
    Stage.PROD: {Stage.DEPRECATED, Stage.STAGING},
    Stage.DEPRECATED: {Stage.RETIRED, Stage.PROD},  # un-deprecate is allowed
    Stage.RETIRED: set(),  # terminal
}


class ApprovalState(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


@dataclass
class Model:
    """A registered model version with metadata and (optional) parent lineage link."""
    version: ModelVersion
    description: str = ""
    parent: Optional[ModelVersion] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    tags: Set[str] = field(default_factory=set)
    created_at: float = field(default_factory=time.time)
    created_by: str = ""

    def __str__(self) -> str:
        return str(self.version)


@dataclass
class Approval:
    """A request to promote a model to a target stage, with audit trail."""
    id: int
    model_version: ModelVersion
    target_stage: Stage
    state: ApprovalState
    requested_by: str
    requested_at: float = field(default_factory=time.time)
    decided_by: Optional[str] = None
    decided_at: Optional[float] = None
    notes: str = ""
