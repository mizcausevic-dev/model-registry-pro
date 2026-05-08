"""Promotion policies: who can approve what, when an auto-approve is allowed."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Protocol, Set

from .model import Stage, ModelVersion


class PromotionPolicy(Protocol):
    """A policy decides whether a stage transition can proceed without explicit approval."""

    def requires_approval(self, model_version: ModelVersion, current: Stage, target: Stage) -> bool:
        ...

    def can_approve(self, approver: str, model_version: ModelVersion, target: Stage) -> bool:
        ...


@dataclass
class DefaultPolicy:
    """
    Sensible defaults:
      - DEV -> STAGING: no approval required (engineers self-promote to staging)
      - STAGING -> PROD: approval required (any approver in `approvers` set)
      - PROD -> DEPRECATED: approval required
      - Anything else: approval required by default
    """
    approvers: Set[str] = field(default_factory=set)
    require_distinct_approver: bool = True  # Approver cannot equal requester

    def requires_approval(self, model_version: ModelVersion, current: Stage, target: Stage) -> bool:
        if current == Stage.DEV and target == Stage.STAGING:
            return False
        return True

    def can_approve(self, approver: str, model_version: ModelVersion, target: Stage) -> bool:
        if not approver:
            return False
        if self.approvers and approver not in self.approvers:
            return False
        return True


@dataclass
class OpenPolicy:
    """No approval required for any transition. Useful for tests/dev environments."""

    def requires_approval(self, model_version: ModelVersion, current: Stage, target: Stage) -> bool:
        return False

    def can_approve(self, approver: str, model_version: ModelVersion, target: Stage) -> bool:
        return True
