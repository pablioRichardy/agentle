from typing import Union
from agentle.generations.providers.amazon.contents.message_start import MessageStart
from agentle.generations.providers.amazon.contents.content_block_start import (
    ContentBlockStart,
)
from agentle.generations.providers.amazon.contents.content_block_delta import (
    ContentBlockDelta,
)
from agentle.generations.providers.amazon.contents.content_block_stop import (
    ContentBlockStop,
)
from agentle.generations.providers.amazon.contents.message_stop import MessageStop
from agentle.generations.providers.amazon.contents.metadata import Metadata

StreamEvent = Union[
    MessageStart,
    ContentBlockStart,
    ContentBlockDelta,
    ContentBlockStop,
    MessageStop,
    Metadata,
]
