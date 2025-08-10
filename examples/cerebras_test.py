from agentle.generations.providers.cerebras.cerebras_generation_provider import (
    CerebrasGenerationProvider,
)


provider = CerebrasGenerationProvider()

generation = provider.generate_by_prompt(
    prompt="Hello, world!",
)

print(generation.text)
