"""Tool registry for the SatQuery agentic workflow."""

from __future__ import annotations
import inspect
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional


@dataclass
class Tool:
    name: str
    description: str
    input_schema: Dict[str, str]
    output_schema: Dict[str, str]
    fn: Callable[..., Any]


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: Dict[str, Tool] = {}

    def register(
        self,
        fn: Callable[..., Any],
        name: Optional[str] = None,
        description: Optional[str] = None,
        input_schema: Optional[Dict[str, str]] = None,
        output_schema: Optional[Dict[str, str]] = None,
    ) -> None:
        tool_name = name or fn.__name__
        tool_desc = description or (fn.__doc__ or "").strip()
        in_schema = input_schema or {
            p: str(param.annotation)
            for p, param in inspect.signature(fn).parameters.items()
        }
        out_schema = output_schema or {"result": "any"}

        self._tools[tool_name] = Tool(
            name=tool_name,
            description=tool_desc,
            input_schema=in_schema,
            output_schema=out_schema,
            fn=fn,
        )

    def get(self, name: str) -> Tool:
        if name not in self._tools:
            raise KeyError(f"Tool '{name}' not found in ToolRegistry")
        return self._tools[name]

    def list_tools(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": t.name,
                "description": t.description,
                "input_schema": t.input_schema,
                "output_schema": t.output_schema,
            }
            for t in self._tools.values()
        ]

    def call(self, name: str, **kwargs: Any) -> Any:
        return self.get(name).fn(**kwargs)


registry = ToolRegistry()


def tool(
    name: Optional[str] = None,
    description: Optional[str] = None,
    input_schema: Optional[Dict[str, str]] = None,
    output_schema: Optional[Dict[str, str]] = None,
):
    def decorator(fn: Callable[..., Any]) -> Callable[..., Any]:
        registry.register(
            fn=fn,
            name=name,
            description=description,
            input_schema=input_schema,
            output_schema=output_schema,
        )
        return fn

    return decorator
