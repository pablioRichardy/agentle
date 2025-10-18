"""
OpenRouter Model Routing Examples

This module demonstrates OpenRouter's model routing features:
1. Auto Router - Automatically selects the best model for your prompt
2. Fallback Models - Automatically tries backup models if primary fails
3. Combining with provider routing for optimal performance
"""

import asyncio
from agentle.generations.providers.openrouter import OpenRouterGenerationProvider
from agentle.generations.models.messages import UserMessage
from agentle.generations.models.message_parts import TextPart


async def example_auto_router():
    """Example: Using OpenRouter's Auto Router.
    
    The Auto Router automatically selects between high-quality models
    based on your prompt, powered by NotDiamond.
    """
    print("\n=== Auto Router Example ===")
    
    # Factory method approach
    provider = OpenRouterGenerationProvider.with_auto_router()
    
    generation = await provider.generate_async(
        messages=[
            UserMessage(parts=[TextPart(text="Explain quantum computing in simple terms")])
        ]
    )
    
    print(f"Selected model: {generation.model}")
    print(f"Response: {generation.text}")


async def example_fallback_models():
    """Example: Using fallback models for reliability.
    
    If the primary model fails (downtime, rate-limiting, moderation),
    OpenRouter automatically tries the fallback models in order.
    """
    print("\n=== Fallback Models Example ===")
    
    # Factory method approach
    provider = OpenRouterGenerationProvider.with_fallback_models(
        fallback_models=[
            "anthropic/claude-3.5-sonnet",
            "gryphe/mythomax-l2-13b"
        ]
    )
    
    # Primary model will be the default, with fallbacks if it fails
    generation = await provider.generate_async(
        model="openai/gpt-4o",
        messages=[
            UserMessage(parts=[TextPart(text="What is the meaning of life?")])
        ]
    )
    
    print(f"Used model: {generation.model}")
    print(f"Response: {generation.text}")


async def example_builder_pattern():
    """Example: Using builder pattern for model routing."""
    print("\n=== Builder Pattern Example ===")
    
    # Start with basic provider and configure
    provider = (
        OpenRouterGenerationProvider()
        .set_fallback_models([
            "anthropic/claude-3.5-sonnet",
            "google/gemini-2.5-flash-preview-09-2025"
        ])
        .order_by_fastest()  # Prioritize throughput
        .enable_zdr()  # Zero data retention
    )
    
    generation = await provider.generate_async(
        model="openai/gpt-4o",
        messages=[
            UserMessage(parts=[TextPart(text="Write a haiku about programming")])
        ]
    )
    
    print(f"Used model: {generation.model}")
    print(f"Response: {generation.text}")


async def example_cost_optimized_with_fallbacks():
    """Example: Cost-optimized setup with quality fallbacks."""
    print("\n=== Cost-Optimized with Fallbacks ===")
    
    provider = (
        OpenRouterGenerationProvider()
        .order_by_cheapest()  # Try cheapest first
        .set_fallback_models([
            "anthropic/claude-3.5-sonnet",  # High-quality fallback
            "openai/gpt-4o"  # Premium fallback
        ])
        .set_max_price(prompt=1.0, completion=3.0)  # Price cap
    )
    
    generation = await provider.generate_async(
        model="google/gemini-2.5-flash-preview-09-2025",
        messages=[
            UserMessage(parts=[TextPart(text="Summarize the theory of relativity")])
        ]
    )
    
    print(f"Used model: {generation.model}")
    print(f"Response: {generation.text}")


async def example_streaming_with_fallbacks():
    """Example: Streaming with model fallbacks."""
    print("\n=== Streaming with Fallbacks ===")
    
    provider = OpenRouterGenerationProvider.with_fallback_models(
        fallback_models=["anthropic/claude-3.5-sonnet"]
    )
    
    print("Streaming response...")
    async for generation in provider.stream_async(
        model="openai/gpt-4o",
        messages=[
            UserMessage(parts=[TextPart(text="Count from 1 to 5")])
        ]
    ):
        if generation.text:
            print(generation.text, end="", flush=True)
    
    print(f"\n\nUsed model: {generation.model}")


async def example_auto_router_with_constraints():
    """Example: Auto Router with provider constraints."""
    print("\n=== Auto Router with Constraints ===")
    
    provider = (
        OpenRouterGenerationProvider.with_auto_router()
        .deny_data_collection()  # Privacy mode
        .enable_zdr()  # Zero data retention
        .filter_by_quantization(["fp16", "bf16"])  # Quality quantization
    )
    
    generation = await provider.generate_async(
        messages=[
            UserMessage(parts=[TextPart(text="Explain machine learning")])
        ]
    )
    
    print(f"Selected model: {generation.model}")
    print(f"Response: {generation.text[:200]}...")


async def main():
    """Run all examples."""
    print("OpenRouter Model Routing Examples")
    print("=" * 50)
    
    # Note: Uncomment the examples you want to run
    # Make sure OPENROUTER_API_KEY is set in your environment
    
    # await example_auto_router()
    # await example_fallback_models()
    # await example_builder_pattern()
    # await example_cost_optimized_with_fallbacks()
    # await example_streaming_with_fallbacks()
    # await example_auto_router_with_constraints()
    
    print("\nAll examples completed!")


if __name__ == "__main__":
    asyncio.run(main())
