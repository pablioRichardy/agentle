import logging
from agentle.generations.providers.amazon.bedrock_generation_provider import (
    BedrockGenerationProvider,
)
from pydantic import BaseModel


class HelloResponse(BaseModel):
    response: str


logging.basicConfig(level=logging.CRITICAL)

provider = BedrockGenerationProvider()

generation = provider.create_generation_by_prompt(
    "Hello!", response_schema=HelloResponse
)

print(generation)
