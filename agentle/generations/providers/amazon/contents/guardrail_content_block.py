from typing import TypedDict, NotRequired, List


class GuardrailContentBlock(TypedDict):
    text: NotRequired[str]
    qualifiers: NotRequired[List[str]]
