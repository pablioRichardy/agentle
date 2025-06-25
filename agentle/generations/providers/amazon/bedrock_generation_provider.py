from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any, Sequence, cast, override

from mypy_boto3_bedrock_runtime.type_defs import ConverseResponseTypeDef

from agentle.generations.collections.message_sequence import MessageSequence
from agentle.generations.models.generation.generation import Generation
from agentle.generations.models.generation.generation_config import GenerationConfig
from agentle.generations.models.generation.generation_config_dict import (
    GenerationConfigDict,
)
from agentle.generations.models.messages.assistant_message import AssistantMessage
from agentle.generations.models.messages.developer_message import DeveloperMessage
from agentle.generations.models.messages.user_message import UserMessage
from agentle.generations.providers.amazon.adapters.agentle_message_to_boto_message import (
    AgentleMessageToBotoMessage,
)
from agentle.generations.providers.amazon.adapters.agentle_tool_to_bedrock_tool_adapter import (
    AgentleToolToBedrockToolAdapter,
)
from agentle.generations.providers.amazon.adapters.generation_config_to_inference_config import (
    GenerationConfigToInferenceConfigAdapter,
)
from agentle.generations.providers.amazon.boto_config import BotoConfig
from agentle.generations.providers.amazon.models.text_content import TextContent
from agentle.generations.providers.amazon.models.tool_config import ToolConfig
from agentle.generations.providers.base.generation_provider import GenerationProvider
from agentle.generations.providers.types.model_kind import ModelKind
from agentle.generations.tools.tool import Tool


@dataclass(frozen=True)
class BedrockGenerationProvider(GenerationProvider):
    region_name: str = field(default="us-east-1")
    config: BotoConfig | None = field(default=None)

    @property
    @override
    def default_model(self) -> str:
        return "anthropic.claude-sonnet-4-20250514-v1:0"

    @property
    @override
    def organization(self) -> str:
        return "aws"

    @override
    async def create_generation_async[T](
        self,
        *,
        model: str | None | ModelKind = None,
        messages: Sequence[AssistantMessage | DeveloperMessage | UserMessage],
        response_schema: type[T] | None = None,
        generation_config: GenerationConfig | GenerationConfigDict | None = None,
        tools: Sequence[Tool[Any]] | None = None,
    ) -> Generation[T]:
        import boto3

        client = boto3.client("bedrock-runtime", region_name=self.region_name)

        message_adapter = AgentleMessageToBotoMessage()

        message_sequence = MessageSequence(messages)

        messages_without_system = message_sequence.without_developer_prompt().elements

        system_message: DeveloperMessage | None = (
            messages_without_system[0]
            if isinstance(messages_without_system[0], DeveloperMessage)
            else None
        )

        conversation = [
            message_adapter.adapt(message) for message in messages_without_system
        ]

        inference_config_adapter = GenerationConfigToInferenceConfigAdapter()
        tool_adapter = AgentleToolToBedrockToolAdapter()

        _inference_config = (
            inference_config_adapter.adapt(generation_config)
            if isinstance(generation_config, GenerationConfig)
            else None
        )

        _tool_config = (
            ToolConfig(
                tools=[tool_adapter.adapt(tool) for tool in tools],
                toolChoice={"auto": {}},
            )
            if tools
            else None
        )

        response: ConverseResponseTypeDef = cast(
            ConverseResponseTypeDef,
            client.converse(
                modelId=model or self.default_model,
                system=[TextContent(text=system_message.text)]
                if system_message
                else None,
                messages=conversation,
                inferenceConfig=_inference_config,
                toolConfig=_tool_config,
            ),
        )

        print(response)

    @override
    def price_per_million_tokens_input(
        self, model: str, estimate_tokens: int | None = None
    ) -> float: ...

    @override
    def price_per_million_tokens_output(
        self, model: str, estimate_tokens: int | None = None
    ) -> float: ...

    @override
    def map_model_kind_to_provider_model(
        self,
        model_kind: ModelKind,
    ) -> str:
        mapping: Mapping[ModelKind, str] = {
            # Stable models
            "category_nano": "",
            "category_mini": "",
            "category_standard": "",
            "category_pro": "",
            "category_flagship": "",
            "category_reasoning": "",
            "category_vision": "",
            "category_coding": "",
            "category_instruct": "",
            # Experimental models
            "category_nano_experimental": "",
            "category_mini_experimental": "",
            "category_standard_experimental": "",
            "category_pro_experimental": "",
            "category_flagship_experimental": "",
            "category_reasoning_experimental": "",
            "category_vision_experimental": "",
            "category_coding_experimental": "",
            "category_instruct_experimental": "",
        }

        return mapping[model_kind]
