from typing import Literal, TypedDict

from agentle.generations.providers.amazon.contents.bytes_source import BytesSource
from agentle.generations.providers.amazon.contents.s3_source import S3Source


class VideoBlock(TypedDict):
    format: Literal["mp4"]
    source: BytesSource | S3Source
