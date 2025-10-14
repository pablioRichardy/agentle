# Adapter for Agentle tool to OpenRouter tool
"""
Adapter for converting Agentle Tool definitions to OpenRouter tool format.

This module handles the conversion of Agentle's Tool objects into
the OpenRouter API tool definition format.
"""

from __future__ import annotations

from typing import override

from rsb.adapters.adapter import Adapter

from agentle.generations.tools.tool import Tool
from agentle.generations.providers.openrouter._types import (
    OpenRouterTool,
    OpenRouterToolFunction,
    OpenRouterToolFunctionParameters,
)


class AgentleToolToOpenRouterToolAdapter(Adapter[Tool, OpenRouterTool]):
    """
    Adapter for converting Agentle Tool objects to OpenRouter format.

    Converts tool definitions including name, description, and parameters
    to the format expected by OpenRouter's API.
    """

    @override
    def adapt(self, tool: Tool) -> OpenRouterTool:
        """
        Convert an Agentle Tool to OpenRouter format.

        Args:
            tool: The Agentle Tool to convert.

        Returns:
            The corresponding OpenRouter tool definition.
        """
        return OpenRouterTool(
            type="function",
            function=OpenRouterToolFunction(
                name=tool.name,
                description=tool.description or "",
                parameters=OpenRouterToolFunctionParameters(
                    type="object",
                    properties=tool.parameters.get("properties", {}),
                    required=tool.parameters.get("required", []),
                ),
            ),
        )
