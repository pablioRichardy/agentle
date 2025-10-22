"""
Example demonstrating Responder with OpenTelemetry (OTel) tracing integration.

This example shows how to use the Responder class with observability clients
to automatically track API calls, usage metrics, and costs. It demonstrates:
- Non-streaming responses with tracing
- Streaming responses with tracing
- Structured output with tracing
- Cost tracking and usage metrics
- Multiple OtelClient support

Requirements:
    - OPENROUTER_API_KEY environment variable set
    - Langfuse configured via environment variables (LANGFUSE_PUBLIC_KEY, LANGFUSE_SECRET_KEY)
      for observability examples

Note: The Langfuse SDK reads credentials from environment variables automatically.
Set these before running:
    export LANGFUSE_PUBLIC_KEY="pk-..."
    export LANGFUSE_SECRET_KEY="sk-..."
    export LANGFUSE_HOST="https://cloud.langfuse.com"  # optional
"""

import asyncio
import os
from pydantic import BaseModel, Field

from agentle.responses.responder import Responder
from agentle.generations.tracing.langfuse_otel_client import LangfuseOtelClient
from agentle.responses.definitions.reasoning import Reasoning, ReasoningEffort


# Define a structured output model
class CityInfo(BaseModel):
    """Information about a city."""

    city: str = Field(description="The name of the city")
    country: str = Field(description="The country where the city is located")
    population: int = Field(description="Approximate population")
    famous_for: list[str] = Field(description="Things the city is famous for")


async def example_non_streaming_without_tracing():
    """Example 1: Basic non-streaming request without tracing."""
    print("\n" + "=" * 80)
    print("Example 1: Non-streaming without tracing")
    print("=" * 80)

    # Create responder without OTel clients
    responder = Responder.from_openrouter()

    # Make a simple request
    response = await responder.respond_async(
        input="What is the capital of France? Answer in one sentence.",
        model="openai/gpt-4o-mini",
        max_output_tokens=100,
    )

    print(f"\nResponse ID: {response.id}")
    print(f"Status: {response.status}")
    print(f"Output: {response.output_text}")

    # Usage information
    if response.usage:
        print("\nUsage:")
        print(f"  Input tokens: {response.usage.input_tokens}")
        print(f"  Output tokens: {response.usage.output_tokens}")
        print(f"  Total tokens: {response.usage.total_tokens}")


async def example_non_streaming_with_tracing():
    """Example 2: Non-streaming request with OTel tracing."""
    print("\n" + "=" * 80)
    print("Example 2: Non-streaming with OTel tracing")
    print("=" * 80)

    # Create OTel client (Langfuse reads credentials from environment)
    otel_client = LangfuseOtelClient()

    # Create responder with OTel client using factory method
    responder = Responder.from_openrouter(otel_clients=[otel_client])

    # Make a request - tracing happens automatically
    response = await responder.respond_async(
        input="Explain quantum computing in simple terms.",
        model="openai/gpt-4o-mini",
        max_output_tokens=200,
        temperature=0.7,
    )

    print(f"\nResponse ID: {response.id}")
    print(f"Status: {response.status}")
    if response.output_text:
        print(f"Output: {response.output_text[:200]}...")

    # Usage and cost information is automatically tracked in Langfuse
    if response.usage:
        print("\nUsage (automatically tracked in observability platform):")
        print(f"  Input tokens: {response.usage.input_tokens}")
        print(f"  Output tokens: {response.usage.output_tokens}")
        print(f"  Total tokens: {response.usage.total_tokens}")

    print("\n✓ Trace created in Langfuse with usage metrics and cost calculations")


async def example_streaming_with_tracing():
    """Example 3: Streaming request with OTel tracing."""
    print("\n" + "=" * 80)
    print("Example 3: Streaming with OTel tracing")
    print("=" * 80)

    # Create OTel client
    otel_client = LangfuseOtelClient()

    # Create responder with OTel client using factory method
    responder = Responder.from_openrouter(otel_clients=[otel_client])

    # Make a streaming request
    stream = await responder.respond_async(
        input="Write a short poem about artificial intelligence.",
        model="openai/gpt-4o-mini",
        max_output_tokens=150,
        stream=True,  # Enable streaming
    )

    print("\nStreaming response:")
    print("-" * 40)

    # Consume the stream
    accumulated_text = ""
    async for event in stream:
        # Handle text delta events
        if event.type == "ResponseTextDeltaEvent":
            delta = event.delta
            print(delta, end="", flush=True)
            accumulated_text += delta

        # Handle completion event
        elif event.type == "ResponseCompletedEvent":
            print("\n" + "-" * 40)
            print(f"\nResponse ID: {event.response.id}")
            print(f"Status: {event.response.status}")

            if event.response.usage:
                print("\nUsage:")
                print(f"  Input tokens: {event.response.usage.input_tokens}")
                print(f"  Output tokens: {event.response.usage.output_tokens}")
                print(f"  Total tokens: {event.response.usage.total_tokens}")

    print("\n✓ Streaming trace created in Langfuse with accumulated metrics")


async def example_structured_output_with_tracing():
    """Example 4: Structured output with OTel tracing."""
    print("\n" + "=" * 80)
    print("Example 4: Structured output with OTel tracing")
    print("=" * 80)

    # Create OTel client
    otel_client = LangfuseOtelClient()

    # Create responder with OTel client using factory method
    responder = Responder.from_openrouter(otel_clients=[otel_client])

    # Make a request with structured output
    response = await responder.respond_async(
        input="Provide information about Tokyo, Japan.",
        model="openai/gpt-4o-mini",
        text_format=CityInfo,  # Request structured output
        max_output_tokens=300,
    )

    print(f"\nResponse ID: {response.id}")
    print(f"Status: {response.status}")

    # Access parsed structured output
    if response.output_parsed:
        city_info = response.output_parsed
        print("\nParsed City Information:")
        print(f"  City: {city_info.city}")
        print(f"  Country: {city_info.country}")
        print(f"  Population: {city_info.population:,}")
        print(f"  Famous for: {', '.join(city_info.famous_for)}")

    # Usage information
    if response.usage:
        print("\nUsage:")
        print(f"  Input tokens: {response.usage.input_tokens}")
        print(f"  Output tokens: {response.usage.output_tokens}")
        print(f"  Total tokens: {response.usage.total_tokens}")

    print("\n✓ Trace created with structured output included in metadata")


async def example_reasoning_with_tracing():
    """Example 5: Request with reasoning enabled and OTel tracing."""
    print("\n" + "=" * 80)
    print("Example 5: Reasoning with OTel tracing")
    print("=" * 80)

    # Create OTel client
    otel_client = LangfuseOtelClient()

    # Create responder with OTel client using factory method
    responder = Responder.from_openrouter(otel_clients=[otel_client])

    # Make a request with reasoning enabled
    response = await responder.respond_async(
        input="Solve this logic puzzle: If all roses are flowers and some flowers fade quickly, can we conclude that some roses fade quickly?",
        model="openai/gpt-4o-mini",
        reasoning=Reasoning(effort=ReasoningEffort.medium),  # Enable reasoning
        max_output_tokens=500,
    )

    print(f"\nResponse ID: {response.id}")
    print(f"Status: {response.status}")
    if response.output_text:
        print(f"Output: {response.output_text}")

    # Usage information with reasoning tokens
    if response.usage:
        print("\nUsage:")
        print(f"  Input tokens: {response.usage.input_tokens}")
        print(f"  Output tokens: {response.usage.output_tokens}")
        print(f"  Total tokens: {response.usage.total_tokens}")

        if response.usage.output_tokens_details:
            reasoning_tokens = response.usage.output_tokens_details.reasoning_tokens
            if reasoning_tokens:
                print(f"  Reasoning tokens: {reasoning_tokens}")

    print("\n✓ Trace created with reasoning tokens tracked separately")


async def example_multiple_otel_clients():
    """Example 6: Using multiple OTel clients simultaneously."""
    print("\n" + "=" * 80)
    print("Example 6: Multiple OTel clients")
    print("=" * 80)

    # Create multiple OTel clients
    langfuse_client = LangfuseOtelClient()

    # You could add more clients here, e.g.:
    # custom_client = CustomOtelClient(...)

    # Create responder with multiple OTel clients using factory method
    responder = Responder.from_openrouter(
        otel_clients=[
            langfuse_client,
            # custom_client,  # Add more clients as needed
        ]
    )

    # Make a request - telemetry sent to all clients
    response = await responder.respond_async(
        input="What are the benefits of observability in AI applications?",
        model="openai/gpt-4o-mini",
        max_output_tokens=200,
    )

    print(f"\nResponse ID: {response.id}")
    if response.output_text:
        print(f"Output: {response.output_text[:200]}...")

    print("\n✓ Traces sent to all configured observability platforms")
    print("  - Langfuse: ✓")
    print("  - (Add more clients as needed)")


async def example_append_otel_client():
    """Example 7: Adding OTel clients dynamically with append_otel_client()."""
    print("\n" + "=" * 80)
    print("Example 7: Dynamically adding OTel clients")
    print("=" * 80)

    # Create responder without OTel clients initially
    responder = Responder.from_openrouter()

    # Later, add observability dynamically
    otel_client = LangfuseOtelClient()
    responder.append_otel_client(otel_client)

    # Make a request - now it will be traced
    response = await responder.respond_async(
        input="What is machine learning?",
        model="openai/gpt-4o-mini",
        max_output_tokens=150,
    )

    print(f"\nResponse ID: {response.id}")
    if response.output_text:
        print(f"Output: {response.output_text[:200]}...")

    print("\n✓ OTel client added dynamically - request was traced")
    print("  - Useful for conditional observability setup")
    print("  - Can add multiple clients at different times")


async def example_error_handling_with_tracing():
    """Example 8: Error handling with OTel tracing."""
    print("\n" + "=" * 80)
    print("Example 8: Error handling with OTel tracing")
    print("=" * 80)

    # Create OTel client
    otel_client = LangfuseOtelClient()

    # Create responder with OTel client using factory method
    responder = Responder.from_openrouter(otel_clients=[otel_client])

    try:
        # Make a request with an invalid model to trigger an error
        await responder.respond_async(
            input="This will fail",
            model="invalid/model-name",  # Invalid model
            max_output_tokens=100,
        )
    except Exception as e:
        print(f"\n✗ Error occurred (as expected): {type(e).__name__}")
        print(f"  Message: {str(e)[:100]}...")
        print("\n✓ Error automatically recorded in observability platform")
        print("  - Error type, message, and timing captured")
        print("  - Trace marked as failed")


async def main():
    """Run all examples."""
    print("\n" + "=" * 80)
    print("Responder OTel Tracing Examples")
    print("=" * 80)

    # Check for required environment variables
    if not os.getenv("OPENROUTER_API_KEY"):
        print("\n⚠ Warning: OPENROUTER_API_KEY not set")
        print("Set it to run these examples:")
        print("  export OPENROUTER_API_KEY='your-key'")
        return

    # Run example without tracing (doesn't require Langfuse)
    await example_non_streaming_without_tracing()

    # Check for Langfuse credentials for tracing examples
    if not os.getenv("LANGFUSE_PUBLIC_KEY") or not os.getenv("LANGFUSE_SECRET_KEY"):
        print("\n" + "=" * 80)
        print("⚠ Langfuse credentials not set - skipping tracing examples")
        print("=" * 80)
        print("\nTo run tracing examples, set:")
        print("  export LANGFUSE_PUBLIC_KEY='pk-...'")
        print("  export LANGFUSE_SECRET_KEY='sk-...'")
        print("  export LANGFUSE_HOST='https://cloud.langfuse.com'  # optional")
        return

    # Run examples with tracing
    await example_non_streaming_with_tracing()
    await example_streaming_with_tracing()
    await example_structured_output_with_tracing()
    await example_reasoning_with_tracing()
    await example_multiple_otel_clients()
    await example_append_otel_client()
    await example_error_handling_with_tracing()

    print("\n" + "=" * 80)
    print("All examples completed!")
    print("=" * 80)
    print("\nCheck your observability platform (e.g., Langfuse) to see:")
    print("  - Traces for each API call")
    print("  - Token usage metrics (input, output, reasoning)")
    print("  - Cost calculations")
    print("  - Latency measurements")
    print("  - Error tracking")
    print("  - Structured output metadata")


if __name__ == "__main__":
    asyncio.run(main())
