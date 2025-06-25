from typing import TypedDict
from agentle.generations.providers.amazon.contents.message_stop_event import (
    MessageStopEvent,
)


class MessageStop(TypedDict):
    stop: MessageStopEvent
