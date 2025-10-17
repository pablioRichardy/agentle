"""
Module for text-based message parts.
"""

from typing import Literal

from rsb.decorators.value_objects import valueobject
from rsb.models.base_model import BaseModel
from rsb.models.field import Field

from agentle.prompts.models.prompt import Prompt


class CacheControl(BaseModel):
    """Cache control for prompt caching (Anthropic-style)."""

    type: Literal["ephemeral"] = Field(default="ephemeral")


@valueobject
class TextPart(BaseModel):
    """
    Represents a plain text part of a message.

    This class is used for textual content within messages in the system.
    """

    type: Literal["text"] = Field(
        default="text",
        description="Discriminator field to identify this as a text message part.",
    )

    text: str | Prompt = Field(description="The textual content of the message part.")

    cache_control: CacheControl | None = Field(
        default=None,
        description="Cache control for prompt caching (Anthropic-style).",
    )

    def __str__(self) -> str:
        return self.text if isinstance(self.text, str) else self.text.text
