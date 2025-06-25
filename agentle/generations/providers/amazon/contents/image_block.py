from typing import Literal, TypedDict

from agentle.generations.providers.amazon.contents.bytes_source import BytesSource
from agentle.generations.providers.amazon.contents.s3_source import S3Source


class ImageBlock(TypedDict):
    format: Literal["jpeg", "png", "gif", "webp"]
    source: BytesSource | S3Source
