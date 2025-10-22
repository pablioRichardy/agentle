"""
Example demonstrating TraceParams integration with Responder.

This example shows how to use TraceParams to add metadata, tags, user_id,
session_id, and other observability information to your API calls.
"""

import asyncio

from dotenv import load_dotenv
from rsb.models.base_model import BaseModel

from agentle.generations.models.generation.trace_params import TraceParams
from agentle.generations.tracing.langfuse_otel_client import LangfuseOtelClient
from agentle.responses.responder import Responder

load_dotenv(override=True)


class Answer(BaseModel):
    """Structured response format."""

    answer: str
    confidence: float


async def basic_trace_params_example():
    """Basic example with trace_params."""
    print("\n=== Basic TraceParams Example ===")

    responder = Responder.openrouter()
    responder.append_otel_client(LangfuseOtelClient())

    # Create trace params with basic information
    trace_params = TraceParams(
        name="customer_support_query",
        user_id="user_123",
        session_id="session_456",
        tags=["support", "billing"],
        metadata={
            "department": "billing",
            "priority": "high",
            "source": "web_chat",
        },
    )

    response = await responder.respond_async(
        input="What is the capital of France?",
        model="google/gemma-3-27b-it",
        max_output_tokens=1000,
        text_format=Answer,
        trace_params=trace_params,
    )

    print(f"Response: {response.output_parsed}")
    print(f"Trace name: {trace_params.get('name')}")
    print(f"User ID: {trace_params.get('user_id')}")
    print(f"Session ID: {trace_params.get('session_id')}")
    print(f"Tags: {trace_params.get('tags')}")


async def version_release_example():
    """Example with version and release tracking."""
    print("\n=== Version & Release Tracking Example ===")

    responder = Responder.openrouter()
    responder.append_otel_client(LangfuseOtelClient())

    # Track version and release information
    trace_params = TraceParams(
        name="api_v2_query",
        version="2.1.0",
        release="production",
        metadata={
            "api_version": "v2",
            "deployment": "us-east-1",
        },
    )

    response = await responder.respond_async(
        input="Explain quantum computing in simple terms",
        model="google/gemma-3-27b-it",
        max_output_tokens=1000,
        trace_params=trace_params,
    )

    print(f"Response: {response.output_text}")
    print(f"Version: {trace_params.get('version')}")
    print(f"Release: {trace_params.get('release')}")


async def multi_user_session_example():
    """Example simulating multiple users and sessions."""
    print("\n=== Multi-User Session Example ===")

    responder = Responder.openrouter()
    responder.append_otel_client(LangfuseOtelClient())

    # Simulate different users asking questions
    users = [
        ("user_alice", "session_001", "What is machine learning?"),
        ("user_bob", "session_002", "Explain neural networks"),
        ("user_charlie", "session_003", "What is deep learning?"),
    ]

    for user_id, session_id, question in users:
        trace_params = TraceParams(
            name="educational_query",
            user_id=user_id,
            session_id=session_id,
            tags=["education", "ai_concepts"],
            metadata={
                "category": "ai_education",
                "difficulty": "beginner",
            },
        )

        response = await responder.respond_async(
            input=question,
            model="google/gemma-3-27b-it",
            max_output_tokens=500,
            trace_params=trace_params,
        )

        print(f"\nUser: {user_id} | Session: {session_id}")
        print(f"Question: {question}")
        print(f"Answer: {response.output_text[:100]}...")


async def streaming_with_trace_params():
    """Example with streaming and trace_params."""
    print("\n=== Streaming with TraceParams Example ===")

    responder = Responder.openrouter()
    responder.append_otel_client(LangfuseOtelClient())

    trace_params = TraceParams(
        name="streaming_query",
        user_id="user_streaming",
        session_id="stream_session_001",
        tags=["streaming", "real_time"],
        metadata={
            "stream_type": "text",
            "buffer_size": "default",
        },
    )

    stream = await responder.respond_async(
        input="Write a short poem about AI",
        model="google/gemma-3-27b-it",
        max_output_tokens=500,
        stream=True,
        trace_params=trace_params,
    )

    print("Streaming response:")
    async for event in stream:
        if event.type == "ResponseTextDeltaEvent":
            print(event.delta, end="", flush=True)

    print("\n")


async def main():
    """Run all examples."""
    await basic_trace_params_example()
    await version_release_example()
    await multi_user_session_example()
    await streaming_with_trace_params()

    print("\n=== All Examples Complete ===")


if __name__ == "__main__":
    asyncio.run(main())
