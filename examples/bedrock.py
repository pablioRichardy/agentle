from agentle.generations.providers.amazon.bedrock_generation_provider import (
    BedrockGenerationProvider,
)


provider = BedrockGenerationProvider("us-east-1")

generation = provider.create_generation_by_prompt_async("Hello!")
