from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ToolParameter:
    name: str
    type: str  
    description: str
    required: bool = True
    default: Any = None
    enum: list[str] | None = None  


@dataclass
class ToolResult:
    success: bool
    output: str
    error: str = ""
    metadata: dict = field(default_factory=dict)


class BaseTool(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        ...

    @property
    @abstractmethod
    def description(self) -> str:
        ...

    @property
    @abstractmethod
    def parameters(self) -> list[ToolParameter]:
        ...

    @abstractmethod
    async def execute(self, **kwargs) -> ToolResult:
        ...

    def to_openai_schema(self) -> dict:
        properties = {}
        required = []

        for param in self.parameters:
            prop: dict[str, object]= {
                "type": param.type,
                "description": param.description,
            }
            if param.enum:
                prop["enum"] = param.enum
            if param.default is not None:
                prop["default"] = param.default

            properties[param.name] = prop

            if param.required:
                required.append(param.name)

        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": properties,
                    "required": required,
                },
            },
        }

    def validate_params(self, **kwargs) -> tuple[bool, str]:
        for param in self.parameters:
            if param.required and param.name not in kwargs:
                return False, f"Missing required parameter: {param.name}"
        return True, ""