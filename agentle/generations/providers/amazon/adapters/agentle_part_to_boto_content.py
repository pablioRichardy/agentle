from typing import override

from rsb.adapters.adapter import Adapter

from agentle.generations.models.message_parts.file import FilePart
from agentle.generations.models.message_parts.text import TextPart
from agentle.generations.models.message_parts.tool_execution_suggestion import (
    ToolExecutionSuggestion,
)
from agentle.generations.providers.amazon.contents.content_block import ContentBlock
from agentle.generations.tools.tool_execution_result import ToolExecutionResult


class AgentlePartToBotoContent(
    Adapter[
        TextPart | FilePart | ToolExecutionSuggestion | ToolExecutionResult,
        ContentBlock,
    ]
):
    @override
    def adapt(
        self, _f: TextPart | FilePart | ToolExecutionSuggestion | ToolExecutionResult
    ) -> ContentBlock: ...
