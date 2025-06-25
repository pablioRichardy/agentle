from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Sequence, override

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
from agentle.generations.providers.amazon.adapters.agentle_part_to_boto_content import (
    AgentlePartToBotoContent,
)
from agentle.generations.providers.amazon.adapters.generation_config_to_inference_config import (
    GenerationConfigToInferenceConfigAdapter,
)
from agentle.generations.providers.amazon.boto_config import BotoConfig
from agentle.generations.providers.base.generation_provider import GenerationProvider
from agentle.generations.providers.types.model_kind import ModelKind
from agentle.generations.tools.tool import Tool


@dataclass(frozen=True)
class BedrockGenerationProvider(GenerationProvider):
    region_name: str
    config: BotoConfig

    @property
    @override
    def default_model(self) -> str:
        return "us.anthropic.claude-sonnet-4-20250514-v1:0"

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

        messages_without_system = (
            MessageSequence(messages).without_developer_prompt().elements
        )

        conversation = [
            message_adapter.adapt(message) for message in messages_without_system
        ]
        inference_config_adapter = GenerationConfigToInferenceConfigAdapter()
        response = client.converse(
            modelId=model or self.default_model,
            messages=conversation,
            inferenceConfig=inference_config_adapter.adapt(
                generation_config
                if isinstance(generation_config, GenerationConfig)
                else GenerationConfig()
            ),
        )

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
