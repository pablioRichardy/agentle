from typing import TypedDict
from agentle.generations.providers.amazon.contents.cache_point_block import (
    CachePointBlock,
)


class CachePointContent(TypedDict):
    cachePoint: CachePointBlock
