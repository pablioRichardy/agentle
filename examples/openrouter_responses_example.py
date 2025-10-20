import asyncio

from dotenv import load_dotenv
from rsb.models.base_model import BaseModel

from agentle.responses.async_stream import AsyncStream
from agentle.responses.definitions.response_completed_event import (
    ResponseCompletedEvent,
)
from agentle.responses.responder import Responder

load_dotenv()


class MathResponse(BaseModel):
    math_result: int


async def main():
    """Basic text generation example."""
    responder = Responder.from_openai()

    print("Starting...")
    response = await responder.respond_async(
        input="What is 2+2?",
        model="gpt-5-nano",
        max_output_tokens=1024,
        text_format=MathResponse,
        stream=True,
    )

    # Help the type checker infer TextFormatT by annotating the stream
    response_stream: AsyncStream[object, MathResponse] = response

    last_completed: ResponseCompletedEvent[MathResponse] | None = None
    async for event in response_stream:
        print(event)
        if isinstance(event, ResponseCompletedEvent):
            last_completed = event

    if last_completed is not None:
        print("Response: ")
        print(last_completed.response)

        print("Output parsed: ")
        parsed = last_completed.response.output_parsed
        print(parsed)


if __name__ == "__main__":
    asyncio.run(main())
