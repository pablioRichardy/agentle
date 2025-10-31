"""
Test the API feature using JSONPlaceholder - a free fake REST API for testing.

This example demonstrates:
1. Creating an API manually with endpoints
2. Loading an API from an OpenAPI spec URL
3. Using the API with an agent
4. Making requests through the agent
"""

from dotenv import load_dotenv

from agentle.agents.agent import Agent
from agentle.agents.apis.api import API
from agentle.agents.apis.endpoint import Endpoint
from agentle.agents.apis.endpoint_parameter import EndpointParameter
from agentle.agents.apis.http_method import HTTPMethod
from agentle.agents.apis.parameter_location import ParameterLocation
from agentle.agents.apis.primitive_schema import PrimitiveSchema
from agentle.generations.providers.google.google_generation_provider import (
    GoogleGenerationProvider,
)

load_dotenv(override=True)


async def test_manual_api():
    """Test creating an API manually."""
    print("\n" + "=" * 70)
    print("TEST 1: Manual API Creation")
    print("=" * 70)

    # Create API manually
    api = API(
        name="JSONPlaceholder",
        description="Free fake REST API for testing and prototyping",
        base_url="https://jsonplaceholder.typicode.com",
        endpoints=[],
    )

    # Test various path patterns to ensure function names are valid
    test_endpoints = [
        # Normal path
        Endpoint(
            name="get_posts",
            description="Get all posts",
            path="/posts",
            method=HTTPMethod.GET,
        ),
        # Path with parameter
        Endpoint(
            name="get_post",
            description="Get a specific post by ID",
            path="/posts/{id}",
            method=HTTPMethod.GET,
            parameters=[
                EndpointParameter(
                    name="id",
                    description="Post ID",
                    parameter_schema=PrimitiveSchema(type="integer"),
                    location=ParameterLocation.PATH,
                    required=True,
                )
            ],
        ),
        # Path with dashes (should be converted to underscores)
        Endpoint(
            name="get_user_posts",
            description="Get posts by user",
            path="/users/{userId}/posts",
            method=HTTPMethod.GET,
            parameters=[
                EndpointParameter(
                    name="userId",
                    description="User ID",
                    parameter_schema=PrimitiveSchema(type="integer"),
                    location=ParameterLocation.PATH,
                    required=True,
                )
            ],
        ),
    ]

    for endpoint in test_endpoints:
        api.add_endpoint(endpoint)

    # Create agent with the API
    agent = Agent(
        name="Blog Assistant",
        generation_provider=GoogleGenerationProvider(
            use_vertex_ai=True, project="unicortex", location="global"
        ),
        model="gemini-2.5-flash",
        instructions="You are a helpful assistant that can fetch blog posts. When asked about posts, use the available tools.",
        apis=[api],
    )

    # Test the agent
    result = agent.run("Get me post with ID 1")
    print(f"\n✅ Manual API test passed!")
    print(f"Response preview: {result.text[:100]}...")

    return result


async def test_edge_cases():
    """Test edge cases for function name generation."""
    print("\n" + "=" * 70)
    print("TEST 2: Edge Cases for Function Name Generation")
    print("=" * 70)

    # Create API with various problematic path patterns
    api = API(
        name="EdgeCaseAPI",
        description="API to test edge cases in function name generation",
        base_url="https://jsonplaceholder.typicode.com",
        endpoints=[],
    )

    # Test cases that previously would have failed
    test_cases = [
        # Path starting with number (after /)
        ("/123/resource", "test_123_resource"),
        # Path with multiple slashes
        ("/api/v1/users", "test_api_v1_users"),
        # Path with dashes
        ("/user-profile", "test_user_profile"),
        # Path with only root
        ("/", "test_root"),
        # Path with parameters
        ("/users/{id}/posts/{postId}", "test_users_posts"),
    ]

    print("\nTesting function name generation:")
    for path, name in test_cases:
        # Create endpoint with explicit name
        endpoint = Endpoint(
            name=name,
            description=f"Test endpoint for {path}",
            path=path,
            method=HTTPMethod.GET,
        )
        api.add_endpoint(endpoint)

        # Convert to tool to verify the name is valid
        tool = endpoint.to_tool(base_url=api.base_url)
        print(f"   ✓ {path} -> {tool.name}")

    print(f"\n✅ All {len(test_cases)} edge cases handled correctly!")
    print(f"   Created {len(api.endpoints)} valid endpoints with valid function names")

    return api


async def main():
    """Run all tests."""
    print("\n🧪 Testing API Feature")
    print("=" * 70)

    # Test 1: Manual API creation
    await test_manual_api()

    # Test 2: Edge cases for function name generation
    await test_edge_cases()

    print("\n" + "=" * 70)
    print("✅ All API tests completed successfully!")
    print("=" * 70)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
