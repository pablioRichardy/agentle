from typing import TypedDict, List, Literal
from agentle.generations.providers.amazon.contents.content_block import ContentBlock


class Message(TypedDict):
    role: Literal["user", "assistant"]
    content: List[ContentBlock]
