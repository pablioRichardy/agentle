# Placeholder for OpenRouter types
"""
Type definitions for OpenRouter API requests and responses.

This module defines TypedDicts for all OpenRouter-specific structures,
ensuring type safety throughout the provider implementation.
"""

from typing import TypedDict, Literal, NotRequired, Sequence


class OpenRouterImageUrl(TypedDict):
    """Image URL structure for OpenRouter messages."""

    url: str
    detail: NotRequired[Literal["auto", "low", "high"]]


class OpenRouterImageUrlPart(TypedDict):
    """Image URL content part."""

    type: Literal["image_url"]
    image_url: OpenRouterImageUrl


class OpenRouterTextPart(TypedDict):
    """Text content part."""

    type: Literal["text"]
    text: str


class OpenRouterFileData(TypedDict):
    """File data structure for PDFs and other documents."""

    filename: str
    file_data: str  # URL or base64 data URL


class OpenRouterFilePart(TypedDict):
    """File content part for PDFs."""

    type: Literal["file"]
    file: OpenRouterFileData


class OpenRouterInputAudioData(TypedDict):
    """Audio data structure."""

    data: str  # base64 encoded audio
    format: Literal["wav", "mp3"]


class OpenRouterInputAudioPart(TypedDict):
    """Audio content part."""

    type: Literal["input_audio"]
    input_audio: OpenRouterInputAudioData


OpenRouterMessageContent = (
    str
    | Sequence[
        OpenRouterTextPart
        | OpenRouterImageUrlPart
        | OpenRouterFilePart
        | OpenRouterInputAudioPart
    ]
)


class OpenRouterToolCallFunction(TypedDict):
    """Function call within a tool call."""

    name: str
    arguments: str  # JSON string


class OpenRouterToolCall(TypedDict):
    """Tool call structure in assistant messages."""

    id: str
    type: Literal["function"]
    function: OpenRouterToolCallFunction


class OpenRouterSystemMessage(TypedDict):
    """System/developer message format."""

    role: Literal["system"]
    content: str


class OpenRouterUserMessage(TypedDict):
    """User message format."""

    role: Literal["user"]
    content: OpenRouterMessageContent


class OpenRouterAssistantMessage(TypedDict):
    """Assistant message format."""

    role: Literal["assistant"]
    content: str | None
    tool_calls: NotRequired[Sequence[OpenRouterToolCall]]


class OpenRouterToolMessage(TypedDict):
    """Tool result message format."""

    role: Literal["tool"]
    tool_call_id: str
    content: str


OpenRouterMessage = (
    OpenRouterSystemMessage
    | OpenRouterUserMessage
    | OpenRouterAssistantMessage
    | OpenRouterToolMessage
)


class OpenRouterToolFunctionParameters(TypedDict):
    """Tool function parameter schema."""

    type: Literal["object"]
    properties: dict[str, object]
    required: NotRequired[Sequence[str]]


class OpenRouterToolFunction(TypedDict):
    """Tool function definition."""

    name: str
    description: str
    parameters: OpenRouterToolFunctionParameters


class OpenRouterTool(TypedDict):
    """Tool definition structure."""

    type: Literal["function"]
    function: OpenRouterToolFunction


class OpenRouterProviderPreferences(TypedDict):
    """Provider routing preferences."""

    allow_fallbacks: NotRequired[bool]
    require_parameters: NotRequired[bool]
    data_collection: NotRequired[Literal["allow", "deny"]]
    order: NotRequired[Sequence[str]]
    quantizations: NotRequired[Sequence[str]]


class OpenRouterJsonSchema(TypedDict):
    """JSON Schema for structured outputs."""

    name: str
    strict: NotRequired[bool]
    schema: dict[str, object]


class OpenRouterResponseFormat(TypedDict):
    """Response format specification for structured outputs."""

    type: Literal["json_schema"]
    json_schema: OpenRouterJsonSchema


class OpenRouterPdfPluginConfig(TypedDict):
    """PDF parsing plugin configuration."""

    engine: NotRequired[Literal["pdf-text", "mistral-ocr", "native"]]


class OpenRouterFileParserPlugin(TypedDict):
    """File parser plugin configuration."""

    id: Literal["file-parser"]
    pdf: NotRequired[OpenRouterPdfPluginConfig]


class OpenRouterUsage(TypedDict):
    """Token usage information."""

    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class OpenRouterResponseMessage(TypedDict):
    """Response message from OpenRouter."""

    role: Literal["assistant"]
    content: str | None
    tool_calls: NotRequired[Sequence[OpenRouterToolCall]]


class OpenRouterChoice(TypedDict):
    """Choice in the response."""

    index: int
    message: OpenRouterResponseMessage
    finish_reason: str


class OpenRouterResponse(TypedDict):
    """Complete response from OpenRouter API."""

    id: str
    provider: NotRequired[str]
    model: str
    object: Literal["chat.completion"]
    created: int
    choices: Sequence[OpenRouterChoice]
    usage: OpenRouterUsage


class OpenRouterRequest(TypedDict):
    """Complete request structure for OpenRouter API."""

    model: str | Sequence[str]
    messages: Sequence[OpenRouterMessage]
    temperature: NotRequired[float]
    max_tokens: NotRequired[int]
    top_p: NotRequired[float]
    frequency_penalty: NotRequired[float]
    presence_penalty: NotRequired[float]
    stream: NotRequired[bool]
    tools: NotRequired[Sequence[OpenRouterTool]]
    tool_choice: NotRequired[Literal["auto", "none"] | dict[str, object]]
    response_format: NotRequired[OpenRouterResponseFormat]
    provider: NotRequired[OpenRouterProviderPreferences]
    plugins: NotRequired[Sequence[OpenRouterFileParserPlugin]]
