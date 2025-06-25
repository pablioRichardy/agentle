from typing import TypedDict, List, Literal
from agentle.generations.providers.amazon.contents.content_block import ContentBlock


class ResponseMessage(TypedDict):
    role: Literal["assistant"]
    content: List[ContentBlock]
