from typing import TypedDict, List, NotRequired, Any
from agentle.generations.providers.amazon.contents.message import Message
from agentle.generations.providers.amazon.contents.system_message import SystemMessage
from agentle.generations.providers.amazon.contents.inference_config import (
    InferenceConfig,
)
from agentle.generations.providers.amazon.contents.tool_config import ToolConfig
from agentle.generations.providers.amazon.contents.guardrail_config import (
    GuardrailConfig,
)


class ConverseRequest(TypedDict):
    modelId: str
    messages: List[Message]
    system: NotRequired[List[SystemMessage]]
    inferenceConfig: NotRequired[InferenceConfig]
    toolConfig: NotRequired[ToolConfig]
    guardrailConfig: NotRequired[GuardrailConfig]
    additionalModelRequestFields: NotRequired[dict[str, Any]]
    additionalModelResponseFieldPaths: NotRequired[List[str]]
