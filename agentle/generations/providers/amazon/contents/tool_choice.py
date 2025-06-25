from collections.abc import Mapping
from typing import TypedDict, NotRequired, Any
from agentle.generations.providers.amazon.contents.specific_tool import SpecificTool


class ToolChoice(TypedDict):
    auto: NotRequired[Mapping[str, Any]]  # Empty dict for auto mode
    any: NotRequired[Mapping[str, Any]]  # Empty dict for any tool mode
    tool: NotRequired[SpecificTool]  # For specific tool selection
