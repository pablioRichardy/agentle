from typing import TypedDict, NotRequired, Any
from agentle.generations.providers.amazon.contents.image_block import ImageBlock
from agentle.generations.providers.amazon.contents.document_block import DocumentBlock


class ToolResultContentBlock(TypedDict):
    text: NotRequired[str]
    json: NotRequired[dict[str, Any]]
    image: NotRequired[ImageBlock]
    document: NotRequired[DocumentBlock]
