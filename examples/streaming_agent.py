import asyncio
from typing import AsyncIterator, cast
from agentle.agents.agent import Agent, WithoutStructuredOutput
from agentle.agents.agent_run_output import AgentRunOutput

from pydantic import BaseModel


class Response(BaseModel):
    reasoning: str
    response: str


async def sum(a: float, b: float) -> float:
    return a + b


async def main():
    agent = Agent()
    
    print("Streaming poem generation...")
    print("=" * 50)
    
    stream_result = await agent.run_async("write a poem about america", stream=True)
    stream_iterator = cast(AsyncIterator[AgentRunOutput[WithoutStructuredOutput]], stream_result)
    async for chunk in stream_iterator:
        # Print each chunk as it arrives
        if chunk.generation and chunk.generation.choices:
            for choice in chunk.generation.choices:
                if choice.message and choice.message.parts:
                    for part in choice.message.parts:
                        if hasattr(part, 'text') and getattr(part, 'text', None):
                            print(str(getattr(part, 'text')), end='', flush=True)
    
    print("\n" + "=" * 50)
    print("Streaming complete!")


if __name__ == "__main__":
    from dotenv import load_dotenv

    load_dotenv()

    asyncio.run(main())
