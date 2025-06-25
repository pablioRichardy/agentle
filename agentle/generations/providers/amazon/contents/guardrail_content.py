from typing import TypedDict
from agentle.generations.providers.amazon.contents.guardrail_content_block import (
    GuardrailContentBlock,
)


class GuardrailContent(TypedDict):
    guardContent: GuardrailContentBlock
