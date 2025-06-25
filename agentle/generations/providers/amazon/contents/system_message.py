from typing import TypedDict, NotRequired
from agentle.generations.providers.amazon.contents.cache_point_block import (
    CachePointBlock,
)


class SystemMessage(TypedDict):
    text: str
    cachePoint: NotRequired[CachePointBlock]
