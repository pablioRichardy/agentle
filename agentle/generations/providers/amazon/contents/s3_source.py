from typing import TypedDict

from agentle.generations.providers.amazon.contents.s3_location import S3Location


class S3Source(TypedDict):
    s3Location: S3Location
