from typing import TypedDict
from agentle.generations.providers.amazon.contents.response_message import (
    ResponseMessage,
)


class ConverseOutput(TypedDict):
    message: ResponseMessage
