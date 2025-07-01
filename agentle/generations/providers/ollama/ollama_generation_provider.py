from __future__ import annotations

import asyncio
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, Sequence, cast, override

from agentle.generations.models.generation.generation import Generation
from agentle.generations.models.generation.generation_config import GenerationConfig
from agentle.generations.models.generation.generation_config_dict import (
    GenerationConfigDict,
)
from agentle.generations.models.messages.assistant_message import AssistantMessage
from agentle.generations.models.messages.developer_message import DeveloperMessage
from agentle.generations.models.messages.user_message import UserMessage
from agentle.generations.providers.base.generation_provider import GenerationProvider
from agentle.generations.providers.ollama.adapters.chat_response_to_generation_adapter import (
    ChatResponseToGenerationAdapter,
)
from agentle.generations.providers.ollama.adapters.tool_to_ollama_tool_adapter import (
    ToolToOllamaToolAdapter,
)
from agentle.generations.providers.types.model_kind import ModelKind
from agentle.generations.tools.tool import Tool
from agentle.generations.tracing.contracts.stateful_observability_client import (
    StatefulObservabilityClient,
)

if TYPE_CHECKING:
    from ollama._types import Options


class OllamaGenerationProvider(GenerationProvider):
    def __init__(
        self,
        *,
        tracing_client: StatefulObservabilityClient | None = None,
        options: Mapping[str, Any] | Options | None = None,
        think: bool | None = None,
        host: str | None = None,
    ) -> None:
        from ollama._client import AsyncClient

        super().__init__(tracing_client=tracing_client)
        self._client = AsyncClient(host=host)
        self.options = options
        self.think = think

    @override
    async def create_generation_async[T](
        self,
        *,
        model: str | ModelKind | None = None,
        messages: Sequence[AssistantMessage | DeveloperMessage | UserMessage],
        response_schema: type[T] | None = None,
        generation_config: GenerationConfig | GenerationConfigDict | None = None,
        tools: Sequence[Tool[Any]] | None = None,
    ) -> Generation[T]:
        from pydantic import BaseModel

        tool_adapter = ToolToOllamaToolAdapter()

        bm = cast(BaseModel, response_schema) if response_schema else None

        _generation_config = self._normalize_generation_config(generation_config)

        _model = self._resolve_model(model)

        async with asyncio.timeout(_generation_config.timeout_in_seconds):
            response = await self._client.chat(
                model=_model,
                tools=[tool_adapter.adapt(tool) for tool in tools] if tools else None,
                format=bm.model_json_schema() if bm else None,
                options=self.options,
                think=self.think,
            )

        return ChatResponseToGenerationAdapter(
            model=_model, response_schema=response_schema
        ).adapt(response)

    @override
    def price_per_million_tokens_input(
        self, model: str, estimate_tokens: int | None = None
    ) -> float:
        return 0.0

    @override
    def price_per_million_tokens_output(
        self, model: str, estimate_tokens: int | None = None
    ) -> float:
        return 0.0

    @override
    def map_model_kind_to_provider_model(
        self,
        model_kind: ModelKind,
    ) -> str:
        return ""
