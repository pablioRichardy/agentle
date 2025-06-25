from typing import Union
from agentle.generations.providers.amazon.contents.text_content_block import TextContent
from agentle.generations.providers.amazon.contents.image_content import ImageContent
from agentle.generations.providers.amazon.contents.document_content import (
    DocumentContent,
)
from agentle.generations.providers.amazon.contents.video_content import VideoContent
from agentle.generations.providers.amazon.contents.tool_use_content import (
    ToolUseContent,
)
from agentle.generations.providers.amazon.contents.tool_result_content import (
    ToolResultContent,
)
from agentle.generations.providers.amazon.contents.guardrail_content import (
    GuardrailContent,
)
from agentle.generations.providers.amazon.contents.cache_point_content import (
    CachePointContent,
)
from agentle.generations.providers.amazon.contents.reasoning_content import (
    ReasoningContent,
)

ContentBlock = Union[
    TextContent,
    ImageContent,
    DocumentContent,
    VideoContent,
    ToolUseContent,
    ToolResultContent,
    GuardrailContent,
    CachePointContent,
    ReasoningContent,
]
