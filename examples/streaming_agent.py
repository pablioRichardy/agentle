import asyncio

from agentle.agents.agent import Agent

import pprint
from pydantic import BaseModel


class Response(BaseModel):
    reasoning: str
    response: str


async def sum(a: float, b: float) -> float:
    return a + b


async def main():
    agent = Agent()
    async for chunk in agent.run_async("write a poem about america", stream=True):
        pprint.pprint(chunk)


if __name__ == "__main__":
    from dotenv import load_dotenv

    load_dotenv()

    asyncio.run(main())
