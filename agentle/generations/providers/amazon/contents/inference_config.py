from typing import TypedDict, NotRequired, List


class InferenceConfig(TypedDict):
    maxTokens: NotRequired[int]
    temperature: NotRequired[float]
    topP: NotRequired[float]
    stopSequences: NotRequired[List[str]]
