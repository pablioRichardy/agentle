# Adapter for Agentle tool to OpenRouter tool
"""
Adapter for converting Agentle Tool definitions to OpenRouter tool format.

This module handles the conversion of Agentle's Tool objects into
the OpenRouter API tool definition format.
"""

from __future__ import annotations

from typing import Any, override, cast

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
    
    This adapter handles both flat parameter format (from Tool.from_callable)
    and JSON Schema format.
    """

    def _convert_to_json_schema(self, agentle_params: dict[str, Any]) -> dict[str, Any]:
        """
        Convert Agentle's flat parameter format to proper JSON Schema format.

        Agentle format:
        {
            'param1': {'type': 'str', 'required': True, 'description': '...'},
            'param2': {'type': 'int', 'required': False, 'default': 42}
        }

        JSON Schema format:
        {
            'type': 'object',
            'properties': {
                'param1': {'type': 'string', 'description': '...'},
                'param2': {'type': 'integer', 'default': 42}
            },
            'required': ['param1']
        }
        
        Args:
            agentle_params: Parameters in Agentle's flat format or JSON Schema format.
            
        Returns:
            Parameters in JSON Schema format.
        """
        # Check if this is already in JSON Schema format
        if "type" in agentle_params and "properties" in agentle_params:
            return agentle_params

        # Check if it's a $schema format (also JSON Schema)
        if "$schema" in agentle_params or "properties" in agentle_params:
            if "type" not in agentle_params:
                result = {"type": "object"}
                result.update(agentle_params)
                return result
            return agentle_params

        # Convert from Agentle flat format to JSON Schema format
        properties: dict[str, Any] = {}
        required: list[str] = []

        # Type mapping from Python types to JSON Schema types
        type_mapping = {
            "str": "string",
            "string": "string",
            "int": "integer",
            "integer": "integer",
            "float": "number",
            "number": "number",
            "bool": "boolean",
            "boolean": "boolean",
            "list": "array",
            "array": "array",
            "dict": "object",
            "object": "object",
        }

        for param_name, param_info in agentle_params.items():
            if not isinstance(param_info, dict):
                continue

            # Extract the parameter info
            param_type_str: str = cast(str, param_info.get("type", "string"))
            is_required = param_info.get("required", False)

            # Create the property schema
            prop_schema: dict[str, Any] = {}

            # Map the type to JSON Schema type
            json_type = type_mapping.get(param_type_str.lower(), param_type_str)
            prop_schema["type"] = json_type

            # Copy over other attributes (excluding 'required' and 'type')
            for key, value in param_info.items():
                if key not in ("required", "type"):
                    prop_schema[key] = value

            properties[param_name] = prop_schema

            if is_required:
                required.append(param_name)

        result: dict[str, Any] = {"type": "object", "properties": properties}

        if required:
            result["required"] = required

        return result

    @override
    def adapt(self, tool: Tool) -> OpenRouterTool:
        """
        Convert an Agentle Tool to OpenRouter format.

        Args:
            tool: The Agentle Tool to convert.

        Returns:
            The corresponding OpenRouter tool definition.
        """
        # Convert parameters to JSON Schema format
        json_schema_params = self._convert_to_json_schema(tool.parameters)
        
        return OpenRouterTool(
            type="function",
            function=OpenRouterToolFunction(
                name=tool.name,
                description=tool.description or "",
                parameters=OpenRouterToolFunctionParameters(
                    type="object",
                    properties=json_schema_params.get("properties", {}),
                    required=json_schema_params.get("required", []),
                ),
            ),
        )
