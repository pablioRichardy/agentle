from typing import TypedDict

from agentle.generations.providers.amazon.contents.content_block_start_event import (
    ContentBlockStartEvent,
)


class ContentBlockStart(TypedDict):
    start: ContentBlockStartEvent
