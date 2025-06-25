from typing import TypedDict, Union
from agentle.generations.providers.amazon.contents.text_delta import TextDelta
from agentle.generations.providers.amazon.contents.tool_use_delta import ToolUseDelta


class ContentBlockDeltaEvent(TypedDict):
    contentBlockIndex: int
    delta: Union[TextDelta, ToolUseDelta]
