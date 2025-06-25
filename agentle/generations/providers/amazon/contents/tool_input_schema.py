from typing import TypedDict, Any


class ToolInputSchema(TypedDict):
    json: dict[str, Any]  # JSON Schema object
