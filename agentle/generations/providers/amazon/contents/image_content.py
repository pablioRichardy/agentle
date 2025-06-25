from typing import TypedDict

from agentle.generations.providers.amazon.contents.image_block import ImageBlock


# Image content block
class ImageContent(TypedDict):
    image: ImageBlock
