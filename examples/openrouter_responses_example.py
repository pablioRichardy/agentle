import asyncio

from dotenv import load_dotenv
from rsb.models.base_model import BaseModel


from agentle.generations.tracing.langfuse_otel_client import LangfuseOtelClient
from agentle.responses.responder import Responder

load_dotenv(override=True)


class MathResponse(BaseModel):
    math_result: int


def add(a: int, b: int) -> int:
    return a + b


async def main():
    """Basic text generation example."""

    responder = Responder.openrouter()
    responder.append_otel_client(LangfuseOtelClient())

    print("Starting...")
    response = await responder.respond_async(
        input="What is 2+2? call the function and also return structured output",
        model="gpt-5-nano",
        max_output_tokens=5000,
        text_format=MathResponse,
    )

    print(response)
    print(response.output_parsed)
    print(response.function_calls)


if __name__ == "__main__":
    asyncio.run(main())
