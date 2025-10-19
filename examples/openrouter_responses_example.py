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

from agentle.responses.open_router.open_router_responder import OpenRouterResponder

load_dotenv()


async def sum_two_numbers(a: float, b: float):
    return a + b


async def main():
    """Basic text generation example."""
    responder = OpenRouterResponder()

    print("Starting...")
    response = await responder.respond_async(
        input="What is 2+2? call the tool",
        model="openai/gpt-5-nano",
        max_output_tokens=500,
        tools=[sum_two_numbers],
    )

    # async for event in response:
    #     print(event)

    print("Response: ")
    print(response)

    print("Function calls: ")
    print(response.function_calls)


if __name__ == "__main__":
    asyncio.run(main())
