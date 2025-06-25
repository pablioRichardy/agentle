from typing import TypedDict, Any


class ToolUseBlock(TypedDict):
    toolUseId: str
    name: str
    input: dict[str, Any]
