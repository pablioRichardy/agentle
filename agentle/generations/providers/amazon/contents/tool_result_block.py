from typing import TypedDict, NotRequired, List, Literal
from agentle.generations.providers.amazon.contents.tool_result_content_block import (
    ToolResultContentBlock,
)


class ToolResultBlock(TypedDict):
    toolUseId: str
    content: List[ToolResultContentBlock]
    status: NotRequired[Literal["success", "error"]]
