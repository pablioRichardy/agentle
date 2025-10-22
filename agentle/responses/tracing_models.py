"""Typed models for tracing context management."""

from __future__ import annotations

from collections.abc import AsyncGenerator
from dataclasses import dataclass
from typing import Any

from agentle.generations.tracing.otel_client import GenerationContext, TraceContext
from agentle.generations.tracing.otel_client_type import OtelClientType


@dataclass
class TraceInputData:
    """Structured input data for trace context."""

    input: str | list[dict[str, Any]] | None
    model: str | None
    has_tools: bool
    tools_count: int
    has_structured_output: bool
    reasoning_enabled: bool
    reasoning_effort: str | None
    temperature: float | None
    top_p: float | None
    max_output_tokens: int | None
    stream: bool

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for API calls."""
        return {
            "input": self.input,
            "model": self.model,
            "has_tools": self.has_tools,
            "tools_count": self.tools_count,
            "has_structured_output": self.has_structured_output,
            "reasoning_enabled": self.reasoning_enabled,
            "reasoning_effort": self.reasoning_effort,
            "temperature": self.temperature,
            "top_p": self.top_p,
            "max_output_tokens": self.max_output_tokens,
            "stream": self.stream,
        }


@dataclass
class TraceMetadata:
    """Metadata for trace context."""

    model: str
    provider: str
    base_url: str
    custom_metadata: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for API calls."""
        result = {
            "model": self.model,
            "provider": self.provider,
            "base_url": self.base_url,
        }
        result.update(self.custom_metadata)
        return result


@dataclass
class UsageDetails:
    """Token usage details from API response."""

    input: int
    output: int
    total: int
    unit: str
    reasoning_tokens: int | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for API calls."""
        result = {
            "input": self.input,
            "output": self.output,
            "total": self.total,
            "unit": self.unit,
        }
        if self.reasoning_tokens is not None and self.reasoning_tokens > 0:
            result["reasoning_tokens"] = self.reasoning_tokens
        return result


@dataclass
class CostDetails:
    """Cost calculation details."""

    input: float
    output: float
    total: float
    currency: str
    input_tokens: int
    output_tokens: int

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for API calls."""
        return {
            "input": self.input,
            "output": self.output,
            "total": self.total,
            "currency": self.currency,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
        }


@dataclass
class TracingContext:
    """Container for a single client's tracing contexts."""

    client: OtelClientType
    trace_gen: AsyncGenerator[TraceContext | None, None]
    trace_ctx: TraceContext | None
    generation_gen: AsyncGenerator[GenerationContext | None, None]
    generation_ctx: GenerationContext | None

    @property
    def client_name(self) -> str:
        """Get the client class name for logging."""
        return type(self.client).__name__
