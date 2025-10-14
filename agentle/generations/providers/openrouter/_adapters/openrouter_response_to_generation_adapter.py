# Adapter for OpenRouter response to generation
"""
Adapter for converting OpenRouter API responses to Agentle Generation objects.

This module handles the transformation of OpenRouter's response format into
Agentle's standardized Generation format, including choices, usage statistics,
and metadata.
"""

from __future__ import annotations

import datetime
import uuid
from typing import override

from rsb.adapters.adapter import Adapter

from agentle.generations.models.generation.choice import Choice
from agentle.generations.models.generation.generation import Generation
from agentle.generations.models.generation.usage import Usage
from agentle.generations.providers.openrouter._adapters.openrouter_message_to_generated_assistant_message_adapter import (
    OpenRouterMessageToGeneratedAssistantMessageAdapter,
)
from agentle.generations.providers.openrouter._types import OpenRouterResponse


class OpenRouterResponseToGenerationAdapter[T](
    Adapter[OpenRouterResponse, Generation[T]]
):
    """
    Adapter for converting OpenRouter responses to Agentle Generation objects.

    Processes the complete response including choices, usage statistics, and
    any structured output data.

    Attributes:
        response_schema: Optional Pydantic model class for parsing structured data.
        preferred_id: Optional UUID to use for the Generation object.
        message_adapter: Adapter for converting response messages.
    """

    response_schema: type[T] | None
    preferred_id: uuid.UUID | None
    message_adapter: OpenRouterMessageToGeneratedAssistantMessageAdapter[T]

    def __init__(
        self,
        *,
        response_schema: type[T] | None = None,
        preferred_id: uuid.UUID | None = None,
        message_adapter: OpenRouterMessageToGeneratedAssistantMessageAdapter[T]
        | None = None,
    ):
        """
        Initialize the adapter.

        Args:
            response_schema: Optional Pydantic model class for structured output.
            preferred_id: Optional UUID to use for the Generation.
            message_adapter: Optional message adapter (created if not provided).
        """
        self.response_schema = response_schema
        self.preferred_id = preferred_id
        self.message_adapter = (
            message_adapter
            or OpenRouterMessageToGeneratedAssistantMessageAdapter(
                response_schema=response_schema
            )
        )

    @override
    def adapt(self, _f: OpenRouterResponse) -> Generation[T]:
        """
        Convert an OpenRouter response to an Agentle Generation.

        Args:
            _f: The OpenRouter API response to convert.

        Returns:
            Generation object with normalized data.
        """
        openrouter_response = _f

        # Convert choices
        choices: list[Choice[T]] = [
            Choice(
                index=choice["index"],
                message=self.message_adapter.adapt(choice["message"]),
            )
            for choice in openrouter_response["choices"]
        ]

        # Extract usage information
        usage_data = openrouter_response["usage"]
        usage = Usage(
            prompt_tokens=usage_data["prompt_tokens"],
            completion_tokens=usage_data["completion_tokens"],
        )

        # Build Generation object
        return Generation(
            id=self.preferred_id or uuid.uuid4(),
            choices=choices,
            object="chat.generation",
            created=datetime.datetime.fromtimestamp(openrouter_response["created"]),
            model=openrouter_response["model"],
            usage=usage,
        )
