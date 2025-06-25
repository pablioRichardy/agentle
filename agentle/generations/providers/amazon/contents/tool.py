from typing import TypedDict
from agentle.generations.providers.amazon.contents.tool_specification import (
    ToolSpecification,
)


class Tool(TypedDict):
    toolSpec: ToolSpecification
