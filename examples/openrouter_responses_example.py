"""
Example usage of OpenRouterResponder with the new Responses API.

This demonstrates:
- Basic text generation
- Streaming responses
- Structured output with Pydantic models
- Tool calling
- Web search integration
- Reasoning capabilities
"""

import asyncio

from dotenv import load_dotenv
from pydantic import BaseModel

from agentle.responses.open_router.open_router_responder import OpenRouterResponder

load_dotenv()


class Response(BaseModel):
    answer: str
    note: str


async def main():
    """Basic text generation example."""
    responder = OpenRouterResponder()

    response = await responder.respond_async(
        input="What is 2+2?",
        model="openai/gpt-5-nano",
        max_output_tokens=500,
        text_format=Response,
        stream=True
    )

    async for event in response:
        print(event)

    # print("Response: ")
    # print(response)

    # print("Output parsed:")
    # print(response.output_parsed)


if __name__ == "__main__":
    asyncio.run(main())
