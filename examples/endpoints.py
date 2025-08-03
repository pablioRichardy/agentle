"""
Real-world examples using public test APIs to demonstrate the endpoint functionality.

This shows how to integrate with actual public APIs using both simple and complex parameters.
"""

import asyncio

from dotenv import load_dotenv

from agentle.agents.agent import Agent
from agentle.agents.apis.api import API
from agentle.agents.apis.array_schema import ArraySchema
from agentle.agents.apis.endpoint import Endpoint
from agentle.agents.apis.http_method import HTTPMethod
from agentle.agents.apis.object_schema import ObjectSchema
from agentle.agents.apis.parameter_location import ParameterLocation
from agentle.agents.apis.params import integer_param, object_param
from agentle.agents.apis.params.array_param import array_param
from agentle.agents.apis.params.string_param import string_param
from agentle.agents.apis.primitive_schema import PrimitiveSchema
from agentle.generations.providers.google.google_generation_provider import (
    GoogleGenerationProvider,
)

load_dotenv()


def example_1_jsonplaceholder_api():
    """
    Example 1: JSONPlaceholder API - A fake REST API for testing
    https://jsonplaceholder.typicode.com/
    """

    # Create a complete API with multiple endpoints
    jsonplaceholder_api = API(
        name="JSONPlaceholder",
        description="Fake REST API for testing and prototyping",
        base_url="https://jsonplaceholder.typicode.com",
        endpoints=[
            # GET all posts
            Endpoint(
                name="get_posts",
                description="Get all blog posts",
                call_condition="when user asks for posts, articles, or blog content",
                path="/posts",
                method=HTTPMethod.GET,
                parameters=[
                    integer_param(
                        name="userId",
                        description="Filter posts by user ID",
                        required=False,
                        location=ParameterLocation.QUERY,
                    ),
                    integer_param(
                        name="_limit",
                        description="Limit number of results",
                        required=False,
                        maximum=100,
                        default=10,
                        location=ParameterLocation.QUERY,
                    ),
                ],
            ),
            # GET specific post
            Endpoint(
                name="get_post",
                description="Get a specific blog post by ID",
                call_condition="when user asks for a specific post or article by ID",
                path="/posts/{postId}",
                method=HTTPMethod.GET,
                parameters=[
                    integer_param(
                        name="postId",
                        description="ID of the post to retrieve",
                        required=True,
                        minimum=1,
                        location=ParameterLocation.PATH,
                    )
                ],
            ),
            # CREATE new post
            Endpoint(
                name="create_post",
                description="Create a new blog post",
                call_condition="when user wants to create, write, or publish a new post",
                path="/posts",
                method=HTTPMethod.POST,
                parameters=[
                    object_param(
                        name="post_data",
                        description="Blog post information",
                        properties={
                            "title": PrimitiveSchema(type="string"),
                            "body": PrimitiveSchema(type="string"),
                            "userId": PrimitiveSchema(type="integer", minimum=1),
                        },
                        required_props=["title", "body", "userId"],
                        location=ParameterLocation.BODY,
                        example={
                            "title": "My New Post",
                            "body": "This is the content of my new post.",
                            "userId": 1,
                        },
                    )
                ],
            ),
            # UPDATE post
            Endpoint(
                name="update_post",
                description="Update an existing blog post",
                call_condition="when user wants to edit, modify, or update a post",
                path="/posts/{postId}",
                method=HTTPMethod.PUT,
                parameters=[
                    integer_param(
                        name="postId",
                        description="ID of the post to update",
                        required=True,
                        location=ParameterLocation.PATH,
                    ),
                    object_param(
                        name="post_updates",
                        description="Updated post information",
                        properties={
                            "title": PrimitiveSchema(type="string"),
                            "body": PrimitiveSchema(type="string"),
                            "userId": PrimitiveSchema(type="integer"),
                        },
                        required_props=["title", "body"],
                        location=ParameterLocation.BODY,
                        example={
                            "title": "Updated Post Title",
                            "body": "This is the updated content.",
                            "userId": 1,
                        },
                    ),
                ],
            ),
            # GET users
            Endpoint(
                name="get_users",
                description="Get all users",
                call_condition="when user asks about users, authors, or people",
                path="/users",
                method=HTTPMethod.GET,
                parameters=[
                    string_param(
                        name="email",
                        description="Filter users by email",
                        required=False,
                        location=ParameterLocation.QUERY,
                    )
                ],
            ),
            # GET comments for a post
            Endpoint(
                name="get_post_comments",
                description="Get comments for a specific post",
                call_condition="when user asks for comments on a post or article",
                path="/posts/{postId}/comments",
                method=HTTPMethod.GET,
                parameters=[
                    integer_param(
                        name="postId",
                        description="ID of the post to get comments for",
                        required=True,
                        location=ParameterLocation.PATH,
                    )
                ],
            ),
        ],
    )

    return jsonplaceholder_api


def example_2_httpbin_testing_api():
    """
    Example 2: HTTPBin API - HTTP Request & Response Service
    https://httpbin.org/
    Great for testing different HTTP methods and parameter types
    """

    httpbin_api = API(
        name="HTTPBin",
        description="HTTP Request & Response Service for testing",
        base_url="https://httpbin.org",
        endpoints=[
            # Test GET with query parameters
            Endpoint(
                name="test_get",
                description="Test GET request with query parameters",
                call_condition="when user wants to test HTTP GET requests",
                path="/get",
                method=HTTPMethod.GET,
                parameters=[
                    string_param(
                        name="param1",
                        description="Test parameter 1",
                        required=False,
                        location=ParameterLocation.QUERY,
                    ),
                    string_param(
                        name="param2",
                        description="Test parameter 2",
                        required=False,
                        location=ParameterLocation.QUERY,
                    ),
                ],
            ),
            # Test POST with JSON body
            Endpoint(
                name="test_post_json",
                description="Test POST request with JSON data",
                call_condition="when user wants to test HTTP POST with JSON",
                path="/post",
                method=HTTPMethod.POST,
                parameters=[
                    object_param(
                        name="json_data",
                        description="JSON data to send",
                        properties={
                            "name": PrimitiveSchema(type="string"),
                            "age": PrimitiveSchema(type="integer", minimum=0),
                            "email": PrimitiveSchema(type="string", format="email"),
                            "preferences": ObjectSchema(
                                properties={
                                    "newsletter": PrimitiveSchema(type="boolean"),
                                    "theme": PrimitiveSchema(
                                        type="string", enum=["light", "dark"]
                                    ),
                                }
                            ),
                            "tags": ArraySchema(items=PrimitiveSchema(type="string")),
                        },
                        required_props=["name", "email"],
                        location=ParameterLocation.BODY,
                        example={
                            "name": "John Doe",
                            "age": 30,
                            "email": "john@example.com",
                            "preferences": {"newsletter": True, "theme": "dark"},
                            "tags": ["developer", "python", "ai"],
                        },
                    )
                ],
            ),
            # Test different HTTP status codes
            Endpoint(
                name="test_status_code",
                description="Test different HTTP status codes",
                call_condition="when user wants to test HTTP status codes",
                path="/status/{code}",
                method=HTTPMethod.GET,
                parameters=[
                    integer_param(
                        name="code",
                        description="HTTP status code to return",
                        required=True,
                        minimum=100,
                        maximum=599,
                        location=ParameterLocation.PATH,
                    )
                ],
            ),
            # Test delay
            Endpoint(
                name="test_delay",
                description="Test request with artificial delay",
                call_condition="when user wants to test request timeouts or delays",
                path="/delay/{seconds}",
                method=HTTPMethod.GET,
                parameters=[
                    integer_param(
                        name="seconds",
                        description="Number of seconds to delay",
                        required=True,
                        minimum=1,
                        maximum=10,
                        location=ParameterLocation.PATH,
                    )
                ],
            ),
        ],
    )

    return httpbin_api


def example_3_cat_facts_api():
    """
    Example 3: Cat Facts API - Simple API with no authentication
    https://catfact.ninja/
    """

    # Individual endpoints (not grouped in API)
    cat_fact_endpoint = Endpoint(
        name="get_cat_fact",
        description="Get a random cat fact",
        call_condition="when user asks about cats, cat facts, or wants cat trivia",
        url="https://catfact.ninja/fact",
        method=HTTPMethod.GET,
        parameters=[
            integer_param(
                name="max_length",
                description="Maximum length of the cat fact",
                required=False,
                minimum=1,
                maximum=1000,
                location=ParameterLocation.QUERY,
            )
        ],
    )

    cat_breeds_endpoint = Endpoint(
        name="get_cat_breeds",
        description="Get information about cat breeds",
        call_condition="when user asks about cat breeds or types of cats",
        url="https://catfact.ninja/breeds",
        method=HTTPMethod.GET,
        parameters=[
            integer_param(
                name="limit",
                description="Number of breeds to return",
                required=False,
                minimum=1,
                maximum=100,
                default=10,
                location=ParameterLocation.QUERY,
            )
        ],
    )

    return [cat_fact_endpoint, cat_breeds_endpoint]


def example_4_rest_countries_api():
    """
    Example 4: REST Countries API - Rich data without authentication
    https://restcountries.com/
    """

    countries_api = API(
        name="RestCountries",
        description="REST Countries API provides country information",
        base_url="https://restcountries.com/v3.1",
        endpoints=[
            # Get all countries
            Endpoint(
                name="get_all_countries",
                description="Get information about all countries",
                call_condition="when user asks about countries, nations, or world geography",
                path="/all",
                method=HTTPMethod.GET,
                parameters=[
                    array_param(
                        name="fields",
                        description="Specific fields to return",
                        item_schema=PrimitiveSchema(
                            type="string",
                            enum=[
                                "name",
                                "capital",
                                "region",
                                "population",
                                "area",
                                "languages",
                                "currencies",
                            ],
                        ),
                        required=False,
                        location=ParameterLocation.QUERY,
                        example=["name", "capital", "population"],
                    )
                ],
            ),
            # Get country by name
            Endpoint(
                name="get_country_by_name",
                description="Get country information by name",
                call_condition="when user asks about a specific country by name",
                path="/name/{country_name}",
                method=HTTPMethod.GET,
                parameters=[
                    string_param(
                        name="country_name",
                        description="Name of the country",
                        required=True,
                        location=ParameterLocation.PATH,
                    ),
                    string_param(
                        name="fullText",
                        description="Search by full name",
                        required=False,
                        enum=["true", "false"],
                        location=ParameterLocation.QUERY,
                    ),
                ],
            ),
            # Get countries by region
            Endpoint(
                name="get_countries_by_region",
                description="Get countries in a specific region",
                call_condition="when user asks about countries in a region like Europe, Asia, etc.",
                path="/region/{region}",
                method=HTTPMethod.GET,
                parameters=[
                    string_param(
                        name="region",
                        description="Region name",
                        required=True,
                        enum=["Africa", "Americas", "Asia", "Europe", "Oceania"],
                        location=ParameterLocation.PATH,
                    )
                ],
            ),
        ],
    )

    return countries_api


async def create_and_test_agents():
    """Create agents with real APIs and test them."""

    # Get the APIs
    jsonplaceholder = example_1_jsonplaceholder_api()
    httpbin = example_2_httpbin_testing_api()
    cat_endpoints = example_3_cat_facts_api()
    countries = example_4_rest_countries_api()

    # Create agents for different use cases

    # 1. Blog management agent
    blog_agent = Agent(
        name="Blog Manager",
        generation_provider=GoogleGenerationProvider(),
        model="gemini-2.5-flash",
        instructions="""You are a blog management assistant. You can:
        - Retrieve and display blog posts
        - Create new blog posts
        - Update existing posts
        - Get information about users and comments
        
        Always provide helpful summaries of the data you retrieve.""",
        apis=[jsonplaceholder],
    )

    # 2. API testing agent
    testing_agent = Agent(
        name="API Tester",
        generation_provider=GoogleGenerationProvider(),
        model="gemini-2.5-flash",
        instructions="""You are an API testing assistant. You can:
        - Test different HTTP methods and status codes
        - Test request delays and timeouts
        - Send various types of data in requests
        
        Explain what each test demonstrates and the results.""",
        apis=[httpbin],
    )

    # 3. Fun facts agent (using individual endpoints)
    facts_agent = Agent(
        name="Fun Facts Assistant",
        generation_provider=GoogleGenerationProvider(),
        model="gemini-2.5-flash",
        instructions="""You are a fun facts assistant. You can provide:
        - Random cat facts and trivia
        - Information about cat breeds
        
        Always make the information engaging and fun!""",
        endpoints=cat_endpoints,
    )

    # 4. Geography agent
    geography_agent = Agent(
        name="Geography Expert",
        generation_provider=GoogleGenerationProvider(),
        model="gemini-2.5-flash",
        instructions="""You are a geography expert. You can provide:
        - Information about countries around the world
        - Regional data and statistics
        - Capital cities, populations, and other country facts
        
        Present information in a clear, educational manner.""",
        apis=[countries],
    )

    # 5. Combined agent with multiple APIs
    super_agent = Agent(
        name="Multi-API Assistant",
        generation_provider=GoogleGenerationProvider(),
        model="gemini-2.5-flash",
        instructions="""You are a versatile assistant with access to multiple APIs:
        - Blog and social media data (JSONPlaceholder)
        - HTTP testing capabilities (HTTPBin)  
        - Fun cat facts and breed information
        - World geography and country data
        
        Use the most appropriate API based on the user's question.""",
        apis=[jsonplaceholder, httpbin, countries],
        endpoints=cat_endpoints,
    )

    return {
        "blog_agent": blog_agent,
        "testing_agent": testing_agent,
        "facts_agent": facts_agent,
        "geography_agent": geography_agent,
        "super_agent": super_agent,
    }


async def run_example_queries():
    """Run example queries against the real APIs."""

    agents = await create_and_test_agents()

    print("=== API Integration Examples with Real Public APIs ===\n")

    # Example 1: Blog management
    print("1. Blog Management Example:")
    try:
        response = await agents["blog_agent"].run_async(
            "Show me the first 3 blog posts, then get details about post #1"
        )
        print(f"Blog Response: {response.safe_generation.text[:500]}...\n")
    except Exception as e:
        print(f"Blog example failed: {e}\n")

    # Example 2: API testing
    print("2. API Testing Example:")
    try:
        response = await agents["testing_agent"].run_async(
            "Test a POST request with JSON data containing my name 'Alice' and email 'alice@example.com'"
        )
        print(f"Testing Response: {response.safe_generation.text[:500]}...\n")
    except Exception as e:
        print(f"Testing example failed: {e}\n")

    # Example 3: Cat facts
    print("3. Fun Cat Facts Example:")
    try:
        response = await agents["facts_agent"].run_async(
            "Tell me an interesting cat fact and information about popular cat breeds"
        )
        print(f"Cat Facts Response: {response.safe_generation.text[:500]}...\n")
    except Exception as e:
        print(f"Cat facts example failed: {e}\n")

    # Example 4: Geography
    print("4. Geography Example:")
    try:
        response = await agents["geography_agent"].run_async(
            "Tell me about France - its capital, population, and region"
        )
        print(f"Geography Response: {response.safe_generation.text[:500]}...\n")
    except Exception as e:
        print(f"Geography example failed: {e}\n")

    # Example 5: Complex multi-API query
    print("5. Multi-API Complex Example:")
    try:
        response = await agents["super_agent"].run_async(
            "Create a blog post about France, include a cat fact, and test that the post creation works properly"
        )
        print(f"Super Agent Response: {response.safe_generation.text[:500]}...\n")
    except Exception as e:
        print(f"Super agent example failed: {e}\n")


def show_api_definitions():
    """Show the API definitions for reference."""

    print("=== API Definitions ===\n")

    # Show JSONPlaceholder API structure
    jsonplaceholder = example_1_jsonplaceholder_api()
    print(f"1. {jsonplaceholder.name}:")
    print(f"   Base URL: {jsonplaceholder.base_url}")
    print(f"   Endpoints: {len(jsonplaceholder.endpoints)}")
    for endpoint in jsonplaceholder.endpoints:
        print(f"   - {endpoint.name}: {endpoint.method.value} {endpoint.path}")
        if endpoint.call_condition:
            print(f"     Call when: {endpoint.call_condition}")
    print()

    # Show HTTPBin API structure
    httpbin = example_2_httpbin_testing_api()
    print(f"2. {httpbin.name}:")
    print(f"   Base URL: {httpbin.base_url}")
    print(f"   Endpoints: {len(httpbin.endpoints)}")
    for endpoint in httpbin.endpoints:
        print(f"   - {endpoint.name}: {endpoint.method.value} {endpoint.path}")
    print()

    # Show individual endpoints
    cat_endpoints = example_3_cat_facts_api()
    print("3. Cat Facts Endpoints:")
    for endpoint in cat_endpoints:
        print(f"   - {endpoint.name}: {endpoint.method.value} {endpoint.url}")
        print(f"     Call when: {endpoint.call_condition}")
    print()

    # Show REST Countries API
    countries = example_4_rest_countries_api()
    print(f"4. {countries.name}:")
    print(f"   Base URL: {countries.base_url}")
    print(f"   Endpoints: {len(countries.endpoints)}")
    for endpoint in countries.endpoints:
        print(f"   - {endpoint.name}: {endpoint.method.value} {endpoint.path}")
    print()


async def main():
    """Main function to run all examples."""

    print("🚀 Real-World API Integration Examples for Agentle\n")
    print(
        "These examples use actual public APIs to demonstrate the endpoint functionality.\n"
    )

    # Show API definitions
    show_api_definitions()

    # Run example queries
    await run_example_queries()

    print("✅ Examples completed!")
    print(
        "\nNote: These examples use real public APIs that should work without authentication."
    )
    print(
        "If any examples fail, it might be due to network issues or API availability."
    )


if __name__ == "__main__":
    # Run the examples
    asyncio.run(main())


# Additional usage patterns for specific scenarios


def create_authenticated_api_example():
    """Example showing how to handle APIs that require authentication."""

    # Example with API key in headers
    weather_api = API(
        name="OpenWeatherMap",
        description="Weather data API",
        base_url="https://api.openweathermap.org/data/2.5",
        headers={"Accept": "application/json"},
        endpoints=[
            Endpoint(
                name="get_current_weather",
                description="Get current weather for a location",
                call_condition="when user asks about current weather conditions",
                path="/weather",
                method=HTTPMethod.GET,
                parameters=[
                    string_param(
                        name="q",
                        description="City name (e.g., 'London,UK')",
                        required=True,
                        location=ParameterLocation.QUERY,
                    ),
                    string_param(
                        name="appid",
                        description="API key",
                        required=True,
                        location=ParameterLocation.QUERY,
                        default="YOUR_API_KEY_HERE",  # Would use env var in practice
                    ),
                    string_param(
                        name="units",
                        description="Temperature units",
                        required=False,
                        enum=["metric", "imperial", "kelvin"],
                        default="metric",
                        location=ParameterLocation.QUERY,
                    ),
                ],
            )
        ],
    )

    return weather_api


def create_complex_object_example():
    """Example showing complex nested objects and arrays."""

    complex_endpoint = Endpoint(
        name="complex_data_submission",
        description="Submit complex nested data structure",
        call_condition="when user wants to submit complex form data",
        url="https://httpbin.org/post",
        method=HTTPMethod.POST,
        parameters=[
            object_param(
                name="submission_data",
                description="Complex form submission",
                properties={
                    "user_info": ObjectSchema(
                        properties={
                            "personal": ObjectSchema(
                                properties={
                                    "first_name": PrimitiveSchema(type="string"),
                                    "last_name": PrimitiveSchema(type="string"),
                                    "birth_date": PrimitiveSchema(
                                        type="string", format="date"
                                    ),
                                }
                            ),
                            "contact": ObjectSchema(
                                properties={
                                    "email": PrimitiveSchema(
                                        type="string", format="email"
                                    ),
                                    "phone": PrimitiveSchema(type="string"),
                                    "addresses": ArraySchema(
                                        items=ObjectSchema(
                                            properties={
                                                "type": PrimitiveSchema(
                                                    type="string", enum=["home", "work"]
                                                ),
                                                "street": PrimitiveSchema(
                                                    type="string"
                                                ),
                                                "city": PrimitiveSchema(type="string"),
                                                "country": PrimitiveSchema(
                                                    type="string"
                                                ),
                                            }
                                        )
                                    ),
                                }
                            ),
                        }
                    ),
                    "preferences": ObjectSchema(
                        properties={
                            "notifications": ArraySchema(
                                items=PrimitiveSchema(type="string")
                            ),
                            "settings": ObjectSchema(
                                properties={
                                    "theme": PrimitiveSchema(type="string"),
                                    "language": PrimitiveSchema(type="string"),
                                }
                            ),
                        }
                    ),
                    "metadata": ObjectSchema(
                        properties={
                            "source": PrimitiveSchema(type="string"),
                            "timestamp": PrimitiveSchema(
                                type="string", format="date-time"
                            ),
                            "tags": ArraySchema(items=PrimitiveSchema(type="string")),
                        }
                    ),
                },
                required_props=["user_info"],
                location=ParameterLocation.BODY,
                example={
                    "user_info": {
                        "personal": {
                            "first_name": "John",
                            "last_name": "Doe",
                            "birth_date": "1990-01-01",
                        },
                        "contact": {
                            "email": "john@example.com",
                            "phone": "+1-555-0123",
                            "addresses": [
                                {
                                    "type": "home",
                                    "street": "123 Main St",
                                    "city": "Anytown",
                                    "country": "USA",
                                }
                            ],
                        },
                    },
                    "preferences": {
                        "notifications": ["email", "push"],
                        "settings": {"theme": "dark", "language": "en"},
                    },
                    "metadata": {
                        "source": "web_form",
                        "timestamp": "2024-01-01T12:00:00Z",
                        "tags": ["new_user", "premium"],
                    },
                },
            )
        ],
    )

    return complex_endpoint
