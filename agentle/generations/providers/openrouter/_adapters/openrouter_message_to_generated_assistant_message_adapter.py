# Adapter for OpenRouter message to generated assistant message
"""
Adapter for converting OpenRouter response messages to Agentle's GeneratedAssistantMessage.

This module handles conversion of OpenRouter's response format into Agentle's
internal GeneratedAssistantMessage format, including structured output parsing.
"""

from __future__ import annotations

import json
from collections.abc import Sequence
from typing import cast

from rsb.adapters.adapter import Adapter
from rsb.models.base_model import BaseModel

from agentle.generations.models.message_parts.text import TextPart
from agentle.generations.models.message_parts.tool_execution_suggestion import (
    ToolExecutionSuggestion,
)
from agentle.generations.models.messages.generated_assistant_message import (
    GeneratedAssistantMessage,
)
from agentle.generations.providers.openrouter._types import (
    OpenRouterResponseMessage,
    OpenRouterToolCall,
)


class OpenRouterMessageToGeneratedAssistantMessageAdapter[T](
    Adapter[
        OpenRouterResponseMessage,
        GeneratedAssistantMessage[T],
    ]
):
    """
    Adapter for converting OpenRouter response messages to GeneratedAssistantMessage.

    Handles conversion of text content, tool calls, and structured output parsing.

    Attributes:
        response_schema: Optional Pydantic model class for parsing structured data.
    """

    response_schema: type[T] | None

    def __init__(self, response_schema: type[T] | None = None):
        """
        Initialize the adapter with an optional response schema.

        Args:
            response_schema: Optional Pydantic model class for parsing structured data.
        """
        self.response_schema = response_schema

    def adapt(
        self,
        _f: OpenRouterResponseMessage,
    ) -> GeneratedAssistantMessage[T]:
        """
        Convert an OpenRouter response message to a GeneratedAssistantMessage.

        Args:
            _f: The OpenRouter response message to convert.

        Returns:
            GeneratedAssistantMessage with content and optional parsed data.
        """
        openrouter_message = _f

        # Extract content
        content = openrouter_message.get("content") or ""

        # Extract tool calls if present
        tool_calls_data: Sequence[OpenRouterToolCall] = openrouter_message.get(
            "tool_calls", []
        )

        # Convert tool calls to ToolExecutionSuggestions
        tool_parts: list[ToolExecutionSuggestion] = []
        for tool_call in tool_calls_data:
            function_data = tool_call.get("function", {})
            tool_parts.append(
                ToolExecutionSuggestion(
                    id=str(tool_call.get("id", "")),
                    tool_name=str(function_data.get("name", "")),
                    args=json.loads(str(function_data.get("arguments", "{}"))),
                )
            )

        # Handle structured output parsing
        parsed_data: T | None = None
        if self.response_schema and content:
            try:
                content_obj = json.loads(content)
                parsed_data = cast(
                    T,
                    cast(BaseModel, self.response_schema).model_validate(content_obj),
                )
            except (json.JSONDecodeError, ValueError):
                # If parsing fails, leave parsed_data as None
                pass

        # Build parts list
        parts: list[TextPart | ToolExecutionSuggestion] = (
            [TextPart(text=content)] if content else []
        )
        parts.extend(tool_parts)

        return GeneratedAssistantMessage[T](
            parts=parts,
            parsed=cast(T, parsed_data),
        )
