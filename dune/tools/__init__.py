from __future__ import annotations
from typing import Dict, Any, Callable, Type, List

class Tool:
    """Base class for all tools."""
    name: str = "tool"
    description: str = ""
    schema: Dict[str, Any] = {}

    def run(self, **kwargs) -> Any:
        raise NotImplementedError

class ToolRegistry:
    """Registry for all tools so the agent can discover and call them."""
    _registry: Dict[str, Type[Tool]] = {}

    @classmethod
    def register(cls, tool_cls: Type[Tool]):
        if not issubclass(tool_cls, Tool):
            raise TypeError("tool_cls must subclass Tool")
        cls._registry[tool_cls.name] = tool_cls
        return tool_cls

    @classmethod
    def get(cls, name: str) -> Type[Tool]:
        return cls._registry[name]

    @classmethod
    def list_tools(cls) -> List[Type[Tool]]:
        return list(cls._registry.values())
    
    @classmethod
    def run(cls, name: str, **kwargs) -> Any:
        tool_cls = cls.get(name)
        tool_instance = tool_cls()
        return tool_instance.run(**kwargs)

# This __all__ is important for the `from . import Tool, ToolRegistry` syntax
__all__ = ["Tool", "ToolRegistry"]
