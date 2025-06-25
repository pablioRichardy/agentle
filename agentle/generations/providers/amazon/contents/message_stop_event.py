from typing import TypedDict, Literal, NotRequired, Any


class MessageStopEvent(TypedDict):
    stopReason: Literal[
        "end_turn",
        "tool_use",
        "max_tokens",
        "stop_sequence",
        "guardrail_intervened",
        "content_filtered",
    ]
    additionalModelResponseFields: NotRequired[dict[str, Any]]
