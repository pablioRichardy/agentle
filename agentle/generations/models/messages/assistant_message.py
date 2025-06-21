"""
Module defining the AssistantMessage class representing messages from assistants.
"""

from collections.abc import Sequence
from typing import Literal

from rsb.models.base_model import BaseModel
from rsb.models.field import Field

from agentle.generations.models.message_parts.file import FilePart
from agentle.generations.models.message_parts.text import TextPart
from agentle.generations.models.message_parts.tool_execution_suggestion import (
    ToolExecutionSuggestion,
)
from agentle.generations.tools.tool_execution_result import ToolExecutionResult


class AssistantMessage(BaseModel):
    """
    Represents a message from an assistant in the system.

    This class can contain a sequence of different message parts including
    text, files, and tool execution suggestions.
    """

    role: Literal["assistant"] = Field(
        default="assistant",
        description="Discriminator field to identify this as an assistant message. Always set to 'assistant'.",
    )

    parts: Sequence[
        TextPart | FilePart | ToolExecutionSuggestion | ToolExecutionResult
    ] = Field(
        description="The sequence of message parts that make up this assistant message.",
    )
