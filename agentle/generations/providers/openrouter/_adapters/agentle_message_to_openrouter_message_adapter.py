# Adapter for Agentle message to OpenRouter message
"""
Adapter for converting Agentle messages to OpenRouter message format.

This module handles the conversion of Agentle's message types
(AssistantMessage, DeveloperMessage, UserMessage) into OpenRouter's
API message format.
"""

from __future__ import annotations

from typing import override

from rsb.adapters.adapter import Adapter

from agentle.generations.models.message_parts.file import FilePart
from agentle.generations.models.message_parts.text import TextPart
from agentle.generations.models.message_parts.tool_execution_suggestion import (
    ToolExecutionSuggestion,
)
from agentle.generations.models.messages.assistant_message import AssistantMessage
from agentle.generations.models.messages.developer_message import DeveloperMessage
from agentle.generations.models.messages.user_message import UserMessage
from agentle.generations.providers.openrouter._adapters.agentle_part_to_openrouter_part_adapter import (
    AgentlePartToOpenRouterPartAdapter,
)
from agentle.generations.providers.openrouter._types import (
    OpenRouterAssistantMessage,
    OpenRouterMessage,
    OpenRouterSystemMessage,
    OpenRouterToolCall,
    OpenRouterUserMessage,
)


class AgentleMessageToOpenRouterMessageAdapter(
    Adapter[
        AssistantMessage | DeveloperMessage | UserMessage,
        OpenRouterMessage,
    ]
):
    """
    Adapter for converting Agentle messages to OpenRouter format.

    Handles conversion of:
    - DeveloperMessage -> OpenRouterSystemMessage
    - UserMessage -> OpenRouterUserMessage
    - AssistantMessage -> OpenRouterAssistantMessage (with tool calls)
    """

    @override
    def adapt(
        self,
        _f: AssistantMessage | DeveloperMessage | UserMessage,
    ) -> OpenRouterMessage:
        """
        Convert an Agentle message to OpenRouter format.

        Args:
            _f: The Agentle message to convert.

        Returns:
            The corresponding OpenRouter message.
        """
        message = _f
        part_adapter = AgentlePartToOpenRouterPartAdapter()

        match message:
            case DeveloperMessage():
                # Developer messages become system messages
                # Concatenate all text parts
                content = "".join(str(p) for p in message.parts)
                return OpenRouterSystemMessage(
                    role="system",
                    content=content,
                )

            case UserMessage():
                # User messages can have multimodal content
                # Filter out non-content parts (like tool execution suggestions)
                content_parts = [
                    p
                    for p in message.parts
                    if not isinstance(p, ToolExecutionSuggestion)
                ]

                # If only text parts, concatenate into a string
                if all(isinstance(p, TextPart) for p in content_parts):
                    return OpenRouterUserMessage(
                        role="user",
                        content="".join(str(p) for p in content_parts),
                    )

                # Otherwise, convert to multimodal format
                return OpenRouterUserMessage(
                    role="user",
                    content=[
                        part_adapter.adapt(p)
                        for p in content_parts
                        if isinstance(p, TextPart) or isinstance(p, FilePart)
                    ],
                )

            case AssistantMessage():
                # Separate text content from tool calls
                text_parts = [p for p in message.parts if isinstance(p, TextPart)]
                tool_suggestions = [
                    p for p in message.parts if isinstance(p, ToolExecutionSuggestion)
                ]

                # Build content string from text parts
                content = "".join(str(p) for p in text_parts) if text_parts else None

                # Convert tool suggestions to OpenRouter tool calls
                tool_calls: list[OpenRouterToolCall] = [
                    OpenRouterToolCall(
                        id=suggestion.id,
                        type="function",
                        function={
                            "name": suggestion.tool_name,
                            "arguments": str(suggestion.args),  # Should be JSON string
                        },
                    )
                    for suggestion in tool_suggestions
                ]

                result = OpenRouterAssistantMessage(
                    role="assistant",
                    content=content,
                )

                if tool_calls:
                    result["tool_calls"] = tool_calls

                return result
