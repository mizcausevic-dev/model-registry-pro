"""ModelRegistry: central catalog with stages, approvals, and lineage."""
from __future__ import annotations
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from .exceptions import (
    ApprovalNotFound, DuplicateModel, InvalidTransition, ModelNotFound, PolicyDenied,
)
from .lineage import LineageGraph
from .model import (
    Approval, ApprovalState, Model, ModelVersion, Stage, VALID_TRANSITIONS,
)
from .policy import DefaultPolicy, PromotionPolicy


@dataclass
class ModelRegistry:
    """Central catalog: register models, query versions, govern stage transitions."""
    policy: PromotionPolicy = field(default_factory=DefaultPolicy)

    _models: Dict[ModelVersion, Model] = field(default_factory=dict, init=False)
    _stages: Dict[ModelVersion, Stage] = field(default_factory=dict, init=False)
    _approvals: Dict[int, Approval] = field(default_factory=dict, init=False)
    _next_approval_id: int = field(default=1, init=False)
    _lineage: LineageGraph = field(default_factory=LineageGraph, init=False)

    # ----- Registration -----

    def register(self, model: Model) -> None:
        if model.version in self._models:
            raise DuplicateModel(f"Already registered: {model.version}")
        if model.parent is not None and model.parent not in self._models:
            raise ModelNotFound(f"Parent not registered: {model.parent}")
        self._models[model.version] = model
        self._stages[model.version] = Stage.DEV
        self._lineage.add(model)

    def get(self, version: ModelVersion) -> Model:
        if version not in self._models:
            raise ModelNotFound(str(version))
        return self._models[version]

    def list_models(self) -> List[Model]:
        return sorted(self._models.values(), key=lambda m: (m.version.name, m.version.version))

    def list_versions(self, name: str) -> List[Model]:
        return sorted(
            (m for m in self._models.values() if m.version.name == name),
            key=lambda m: m.version.version,
        )

    # ----- Stages -----

    def stage_of(self, version: ModelVersion) -> Stage:
        if version not in self._stages:
            raise ModelNotFound(str(version))
        return self._stages[version]

    def production_version(self, name: str) -> Optional[Model]:
        for model in self.list_versions(name):
            if self._stages.get(model.version) == Stage.PROD:
                return model
        return None

    def by_stage(self, stage: Stage) -> List[Model]:
        return sorted(
            (self._models[v] for v, s in self._stages.items() if s == stage),
            key=lambda m: (m.version.name, m.version.version),
        )

    # ----- Approvals / promotion workflow -----

    def request_promotion(
        self, version: ModelVersion, target: Stage, requested_by: str, notes: str = ""
    ) -> Approval:
        if version not in self._models:
            raise ModelNotFound(str(version))
        if not requested_by:
            raise ValueError("requested_by is required")

        current = self._stages[version]
        if target not in VALID_TRANSITIONS[current]:
            raise InvalidTransition(f"{current.value} -> {target.value} not allowed")

        # Auto-promote when policy doesn't require approval
        if not self.policy.requires_approval(version, current, target):
            self._stages[version] = target
            approval = Approval(
                id=self._next_approval_id,
                model_version=version,
                target_stage=target,
                state=ApprovalState.APPROVED,
                requested_by=requested_by,
                decided_by=requested_by,
                decided_at=time.time(),
                notes=notes,
            )
            self._approvals[approval.id] = approval
            self._next_approval_id += 1
            return approval

        approval = Approval(
            id=self._next_approval_id,
            model_version=version,
            target_stage=target,
            state=ApprovalState.PENDING,
            requested_by=requested_by,
            notes=notes,
        )
        self._approvals[approval.id] = approval
        self._next_approval_id += 1
        return approval

    def approve(self, approval_id: int, approved_by: str, notes: str = "") -> Approval:
        approval = self._approvals.get(approval_id)
        if approval is None:
            raise ApprovalNotFound(f"id={approval_id}")
        if approval.state != ApprovalState.PENDING:
            raise InvalidTransition(f"Approval is already {approval.state.value}")
        if not self.policy.can_approve(approved_by, approval.model_version, approval.target_stage):
            raise PolicyDenied(f"{approved_by!r} not authorized to approve")
        # Distinct approver check (configurable on DefaultPolicy)
        require_distinct = getattr(self.policy, "require_distinct_approver", False)
        if require_distinct and approved_by == approval.requested_by:
            raise PolicyDenied("Approver must differ from requester")

        # Apply the stage change
        current = self._stages[approval.model_version]
        if approval.target_stage not in VALID_TRANSITIONS[current]:
            raise InvalidTransition(
                f"Stage drifted: {current.value} -> {approval.target_stage.value} no longer valid"
            )
        self._stages[approval.model_version] = approval.target_stage

        approval.state = ApprovalState.APPROVED
        approval.decided_by = approved_by
        approval.decided_at = time.time()
        if notes:
            approval.notes = (approval.notes + "\n" + notes).strip() if approval.notes else notes
        return approval

    def reject(self, approval_id: int, decided_by: str, notes: str = "") -> Approval:
        approval = self._approvals.get(approval_id)
        if approval is None:
            raise ApprovalNotFound(f"id={approval_id}")
        if approval.state != ApprovalState.PENDING:
            raise InvalidTransition(f"Approval is already {approval.state.value}")
        approval.state = ApprovalState.REJECTED
        approval.decided_by = decided_by
        approval.decided_at = time.time()
        if notes:
            approval.notes = (approval.notes + "\n" + notes).strip() if approval.notes else notes
        return approval

    def pending_approvals(self) -> List[Approval]:
        return sorted(
            (a for a in self._approvals.values() if a.state == ApprovalState.PENDING),
            key=lambda a: a.requested_at,
        )

    def approval_history(self, version: ModelVersion) -> List[Approval]:
        return sorted(
            (a for a in self._approvals.values() if a.model_version == version),
            key=lambda a: a.requested_at,
        )

    # ----- Lifecycle terminal moves -----

    def deprecate(self, version: ModelVersion) -> None:
        current = self.stage_of(version)
        if Stage.DEPRECATED not in VALID_TRANSITIONS[current]:
            raise InvalidTransition(f"Cannot deprecate from {current.value}")
        self._stages[version] = Stage.DEPRECATED

    def retire(self, version: ModelVersion) -> None:
        current = self.stage_of(version)
        if Stage.RETIRED not in VALID_TRANSITIONS[current]:
            raise InvalidTransition(f"Cannot retire from {current.value}")
        self._stages[version] = Stage.RETIRED

    # ----- Lineage -----

    def lineage(self) -> LineageGraph:
        return self._lineage

    def ancestors(self, version: ModelVersion) -> List[Model]:
        return [self._models[v] for v in self._lineage.ancestors(version) if v in self._models]

    def descendants(self, version: ModelVersion) -> List[Model]:
        return [self._models[v] for v in self._lineage.descendants(version) if v in self._models]
