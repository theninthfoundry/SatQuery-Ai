"""
Tool registry for the SatQuery AI agent.

Every capability the agent can invoke (VQA, detection, change detection,
SAR corroboration, etc.) is registered here as a Tool with a typed
input/output schema. The agent router never touches pixels directly —
it only ever calls a registered tool and passes structured facts forward.
This is what keeps hallucination surface area small: the LLM composes a
sentence from facts a tool produced, it doesn't invent the facts.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict


@dataclass
class Tool:
    name: str
    description: str
    input_schema: Dict[str, str]
    output_schema: Dict[str, str]
    fn: Callable[..., Dict[str, Any]]


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: Dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        if tool.name in self._tools:
            raise ValueError(f"Tool '{tool.name}' is already registered")
        self._tools[tool.name] = tool

    def get(self, name: str) -> Tool:
        try:
            return self._tools[name]
        except KeyError as exc:
            raise KeyError(f"No tool registered under '{name}'") from exc

    def list_tools(self) -> Dict[str, Tool]:
        return dict(self._tools)

    def call(self, name: str, **kwargs: Any) -> Dict[str, Any]:
        tool = self.get(name)
        return tool.fn(**kwargs)


registry = ToolRegistry()


def tool(name: str, description: str, input_schema: Dict[str, str], output_schema: Dict[str, str]):
    """Decorator: register a plain function as a tool the agent can call."""

    def decorator(fn: Callable[..., Dict[str, Any]]):
        registry.register(
            Tool(
                name=name,
                description=description,
                input_schema=input_schema,
                output_schema=output_schema,
                fn=fn,
            )
        )
        return fn

    return decorator
