from typing import TypedDict
from agentle.generations.providers.amazon.contents.tool_result_block import (
    ToolResultBlock,
)


class ToolResultContent(TypedDict):
    toolResult: ToolResultBlock
