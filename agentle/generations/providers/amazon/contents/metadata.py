from typing import TypedDict
from agentle.generations.providers.amazon.contents.usage import Usage
from agentle.generations.providers.amazon.contents.converse_metrics import (
    ConverseMetrics,
)


class Metadata(TypedDict):
    usage: Usage
    metrics: ConverseMetrics
