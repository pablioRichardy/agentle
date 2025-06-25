from typing import TypedDict
from agentle.generations.providers.amazon.contents.content_block_stop_event import (
    ContentBlockStopEvent,
)


class ContentBlockStop(TypedDict):
    stop: ContentBlockStopEvent
