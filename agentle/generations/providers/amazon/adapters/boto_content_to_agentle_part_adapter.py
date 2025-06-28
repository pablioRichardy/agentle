from __future__ import annotations

from typing import TYPE_CHECKING, override

from rsb.adapters.adapter import Adapter

from agentle.generations.models.message_parts.text import TextPart
from agentle.generations.models.message_parts.tool_execution_suggestion import (
    ToolExecutionSuggestion,
)

if TYPE_CHECKING:
    from mypy_boto3_bedrock_runtime.type_defs import ContentBlockOutputTypeDef


class BotoContentToAgentlePartAdapter(
    Adapter[
        ContentBlockOutputTypeDef,
        TextPart | ToolExecutionSuggestion,
    ]
):
    @override
    def adapt(
        self,
        _f: ContentBlockOutputTypeDef,
    ) -> TextPart | ToolExecutionSuggestion: ...
