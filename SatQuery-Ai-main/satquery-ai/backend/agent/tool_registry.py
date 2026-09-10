"""Tool capability contracts and registry for the SatQuery agentic workflow.

Enables mathematical reasoning over tool capabilities, preconditions,
postconditions, and memory requirements.
"""

from __future__ import annotations

import inspect
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional


@dataclass
class ToolSpec:
    """Formal capability specification for an agent tool or perception model."""
    name: str
    description: str
    accepts: Dict[str, Any] = field(default_factory=dict)
    requires: List[str] = field(default_factory=list)
    produces: List[str] = field(default_factory=list)
    deterministic: bool = True
    memory_mb: int = 500
    fn: Optional[Callable[..., Any]] = None

    def can_handle(self, modalities: List[str], asset_count: int, is_temporal: bool = False) -> bool:
        """Check if tool can handle the given asset configuration."""
        acc_mods = self.accepts.get("modalities", [])
        if acc_mods and not any(m in acc_mods for m in modalities):
            return False
        min_assets = self.accepts.get("min_assets", self.accepts.get("asset_count", 1))
        if asset_count < min_assets:
            return False
        if is_temporal and not self.accepts.get("temporal", False):
            return False
        return True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "accepts": self.accepts,
            "requires": self.requires,
            "produces": self.produces,
            "deterministic": self.deterministic,
            "memory_mb": self.memory_mb,
        }


# Backward compatibility alias
Tool = ToolSpec


class ToolRegistry:
    """Registry managing capability-matched tools for mission planning."""

    def __init__(self) -> None:
        self._tools: Dict[str, ToolSpec] = {}

    def register(
        self,
        fn: Optional[Callable[..., Any]] = None,
        name: Optional[str] = None,
        description: Optional[str] = None,
        accepts: Optional[Dict[str, Any]] = None,
        requires: Optional[List[str]] = None,
        produces: Optional[List[str]] = None,
        deterministic: bool = True,
        memory_mb: int = 500,
        spec: Optional[ToolSpec] = None,
    ) -> None:
        if spec is not None:
            self._tools[spec.name] = spec
            return

        tool_name = name or (fn.__name__ if fn else "unnamed_tool")
        tool_desc = description or ((fn.__doc__ or "").strip() if fn else "")

        self._tools[tool_name] = ToolSpec(
            name=tool_name,
            description=tool_desc,
            accepts=accepts or {},
            requires=requires or [],
            produces=produces or [],
            deterministic=deterministic,
            memory_mb=memory_mb,
            fn=fn,
        )

    def _ensure_tools_loaded(self) -> None:
        if not self._tools:
            try:
                from . import tools  # noqa: F401
            except Exception:
                pass

    def get(self, name: str) -> ToolSpec:
        self._ensure_tools_loaded()
        if name not in self._tools:
            raise KeyError(f"Tool '{name}' not found in ToolRegistry")
        return self._tools[name]

    def list_tools(self) -> List[Dict[str, Any]]:
        self._ensure_tools_loaded()
        return [t.to_dict() for t in self._tools.values()]

    def find_tools(
        self,
        modality: Optional[str] = None,
        required_production: Optional[str] = None,
        max_memory_mb: Optional[int] = None,
    ) -> List[ToolSpec]:
        """Query registry for tools satisfying capability constraints."""
        self._ensure_tools_loaded()
        matches = []
        for t in self._tools.values():
            if modality and modality not in t.accepts.get("modalities", [modality]):
                continue
            if required_production and required_production not in t.produces:
                continue
            if max_memory_mb and t.memory_mb > max_memory_mb:
                continue
            matches.append(t)
        return matches

    def call(self, name: str, **kwargs: Any) -> Any:
        tool = self.get(name)
        if not tool.fn:
            raise NotImplementedError(f"Tool '{name}' has no executable function bound")
        return tool.fn(**kwargs)


registry = ToolRegistry()


def tool(
    name: Optional[str] = None,
    description: Optional[str] = None,
    accepts: Optional[Dict[str, Any]] = None,
    requires: Optional[List[str]] = None,
    produces: Optional[List[str]] = None,
    deterministic: bool = True,
    memory_mb: int = 500,
):
    def decorator(fn: Callable[..., Any]) -> Callable[..., Any]:
        registry.register(
            fn=fn,
            name=name,
            description=description,
            accepts=accepts,
            requires=requires,
            produces=produces,
            deterministic=deterministic,
            memory_mb=memory_mb,
        )
        return fn

    return decorator
