"""Lineage graph: ancestor / descendant queries on model versions."""
from __future__ import annotations
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set

from .model import Model, ModelVersion


@dataclass
class LineageGraph:
    """
    Tracks parent -> child relationships between model versions.

    Each model can have at most ONE parent (a model is derived from a single base)
    but a parent can have many children.
    """
    _parent: Dict[ModelVersion, Optional[ModelVersion]] = field(default_factory=dict)
    _children: Dict[ModelVersion, Set[ModelVersion]] = field(
        default_factory=lambda: defaultdict(set)
    )

    def add(self, model: Model) -> None:
        self._parent[model.version] = model.parent
        if model.parent is not None:
            self._children[model.parent].add(model.version)

    def remove(self, version: ModelVersion) -> None:
        parent = self._parent.pop(version, None)
        if parent is not None:
            self._children[parent].discard(version)
        # Orphan any children
        for child in list(self._children.get(version, set())):
            self._parent[child] = None
        self._children.pop(version, None)

    def parent_of(self, version: ModelVersion) -> Optional[ModelVersion]:
        return self._parent.get(version)

    def children_of(self, version: ModelVersion) -> List[ModelVersion]:
        return sorted(self._children.get(version, set()), key=lambda v: (v.name, v.version))

    def ancestors(self, version: ModelVersion) -> List[ModelVersion]:
        """Return chain from immediate parent up to the root (excluding `version` itself)."""
        chain: List[ModelVersion] = []
        seen: Set[ModelVersion] = set()
        current = self._parent.get(version)
        while current is not None and current not in seen:
            chain.append(current)
            seen.add(current)
            current = self._parent.get(current)
        return chain

    def descendants(self, version: ModelVersion) -> List[ModelVersion]:
        """BFS over all derived versions (excluding `version` itself)."""
        result: List[ModelVersion] = []
        seen: Set[ModelVersion] = set()
        queue = list(self._children.get(version, set()))
        while queue:
            current = queue.pop(0)
            if current in seen:
                continue
            seen.add(current)
            result.append(current)
            queue.extend(self._children.get(current, set()))
        return sorted(result, key=lambda v: (v.name, v.version))
