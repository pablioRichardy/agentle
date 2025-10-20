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
import os

from dotenv import load_dotenv
from rsb.models.base_model import BaseModel

from agentle.responses.open_router.open_router_responder import OpenRouterResponder
from agentle.responses.definitions.response_completed_event import (
    ResponseCompletedEvent,
)

load_dotenv()


class MathResponse(BaseModel):
    math_result: int


async def main():
    """Basic text generation example."""
    responder = OpenRouterResponder(api_key=os.getenv("OPENAI_API_KEY"))

    print("Starting...")
    response = await responder.respond_async(
        input="What is 2+2?",
        model="gpt-5-nano",
        max_output_tokens=1024,
        text_format=MathResponse,
        stream=True,
    )

    last_completed: ResponseCompletedEvent | None = None
    async for event in response:
        print(event)
        if isinstance(event, ResponseCompletedEvent):
            last_completed = event

    if last_completed is not None:
        print("Response: ")
        print(last_completed.response)

        print("Output parsed: ")
        print(last_completed.response.output_parsed)


if __name__ == "__main__":
    asyncio.run(main())
