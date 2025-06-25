from typing import TypedDict
from agentle.generations.providers.amazon.contents.reasoning_content_block import (
    ReasoningContentBlock,
)


class ReasoningContent(TypedDict):
    reasoningContent: ReasoningContentBlock
