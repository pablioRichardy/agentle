from typing import TypedDict, List, NotRequired
from agentle.generations.providers.amazon.contents.tool import Tool
from agentle.generations.providers.amazon.contents.tool_choice import ToolChoice


class ToolConfig(TypedDict):
    tools: List[Tool]
    toolChoice: NotRequired[ToolChoice]
