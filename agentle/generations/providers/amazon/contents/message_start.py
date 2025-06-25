from typing import TypedDict
from agentle.generations.providers.amazon.contents.message_start_event import (
    MessageStartEvent,
)


class MessageStart(TypedDict):
    start: MessageStartEvent
