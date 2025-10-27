"""
Providers Example

This example demonstrates how to use different model providers with the Agentle framework.
"""

import asyncio
from dotenv import load_dotenv
from rsb.models.base_model import BaseModel


from agentle.generations.models.message_parts.text import TextPart
from agentle.generations.models.messages.user_message import UserMessage
from agentle.generations.providers.base.generation_provider import GenerationProvider
from agentle.generations.providers.google.google_generation_provider import (
    GoogleGenerationProvider,
)

load_dotenv()


class PoemResponse(BaseModel):
    poem: str


# Example 1: Create an agent with Google's Gemini model
provider: GenerationProvider = GoogleGenerationProvider()


async def main() -> None:
    # Run the Google agent
    stream = provider.stream_async(
        model="google/gemini-2.5-flash",
        messages=[
            UserMessage(
                parts=[
                    TextPart(
                        text="Escreva um poema sobre o amor",
                    ),
                ]
            )
        ],
        response_schema=PoemResponse,
    )

    async for generation in stream:
        print(generation)
        print()
        print()
        print()


if __name__ == "__main__":
    asyncio.run(main())
