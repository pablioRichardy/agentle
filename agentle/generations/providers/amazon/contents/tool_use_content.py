from typing import TypedDict
from agentle.generations.providers.amazon.contents.tool_use_block import ToolUseBlock


class ToolUseContent(TypedDict):
    toolUse: ToolUseBlock
