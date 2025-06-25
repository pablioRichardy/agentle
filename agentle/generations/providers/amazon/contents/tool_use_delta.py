from typing import TypedDict
from agentle.generations.providers.amazon.contents.tool_use_delta_block import (
    ToolUseDeltaBlock,
)


class ToolUseDelta(TypedDict):
    toolUse: ToolUseDeltaBlock
