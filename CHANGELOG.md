# Changelog

## 🚀 v0.8.0 - Enhanced Tools & Streaming
### ✨ Major Features

#### 🔧 Enhanced Tool System
- **feat**: Tool integrations with improved error handling
- **feat**: Added `ignore_errors` flag to handle tool execution failures gracefully
- **feat**: New "from_openai_spec" method in the `API` class for seamless OpenAI integration
- **refactor**: Improved type safety with ParamSpec and TypeVar for better tool call interface
- **refactor**: Simplified tool call interface by removing context parameter

#### 🤖 Agent Capabilities
- **feat**: Agent serialization support for persistent state management
- **feat**: Performance metrics integration for monitoring agent execution
- **feat**: Dynamic agent modification methods:
  - `change_instructions()` - Modify agent instructions on the fly
  - `change_name()`, `change_apis()`, `change_endpoints()` - Update agent properties
  - `append_instructions()` - Add to existing instructions
  ```python
  # Dynamic instruction modification
  agent.change_instructions("You are now a helpful coding assistant")
  agent.append_instructions("Always provide code examples")
  agent.change_name("CodeHelper")
  ```
- **feat**: Synchronous streaming support in `agent.run()` with background thread implementation
- **feat**: Enhanced conversation history handling with `replace_message_history()` method
  ```python
  # Replace conversation history while preserving developer messages
  context.replace_message_history(
      new_history=[user_message, assistant_message],
      keep_developer_messages=True
  )
  ```
- **feat**: Support for cloning and updating assistant messages

#### 🌐 API & Endpoints
- **feat**: JSON schema support for endpoint parameters with comprehensive type conversion
- **feat**: Endpoints system for structured API interactions
- **feat**: Enhanced API configuration and management

#### 📡 Integrations & Providers
- **feat**: Langfuse integration for advanced analytics
- **feat**: OpenTelemetry support for distributed tracing
- **feat**: Anti-spam protection in Evolution API provider
- **feat**: WhatsApp integration improvements with `with_overrides()` method in `WhatsAppBotConfig`
  ```python
  # Flexible configuration overrides
  base_config = WhatsAppBotConfig.production()
  custom_config = base_config.with_overrides(
      debug_mode=True,
      typing_duration=2,
      welcome_message="Welcome to our enhanced support!",
      max_messages_per_minute=50
  )
  ```

#### 🔄 Streaming & Async
- **feat**: Comprehensive streaming support with text chunk accumulation
  ```python
  # Streaming with accumulated text chunks
  async for chunk in agent.run_stream_async("Generate a poem"):
      # Each chunk contains accumulated text up to that point
      accumulated_text = chunk.generation.text
      print(f"Current text: {accumulated_text}")
  ```
- **feat**: Async streaming examples and improved async handling
- **feat**: Better streaming output handling with proper typing

### 🐛 Critical Fixes

#### 🔧 Tool Execution
- **fix**: Ensured tool results immediately follow tool calls in message history
  ```python
  # Proper tool execution flow
  tool_results = []
  for tool_call in generation.tool_calls:
      result = await tool.call_async(tool_call.arguments)
      tool_results.append(ToolExecutionResult(
          tool_call_id=tool_call.id,
          result=result,
          error=None if result.success else result.error
      ))
  # Results immediately follow tool calls in message history
  ```
- **fix**: Unique tool suggestion IDs and proper message history validation
- **fix**: Google function calling 400 error resolution using ToolExecutionResult
- **fix**: Tool calls and function response logic issues

#### 🤖 Agent Behavior
- **fix**: Redundant message appends and inline tool generation messages
- **fix**: Empty tool generation message handling in streaming
- **fix**: Proper conversation handling to prevent duplicate welcome messages
- **fix**: Corrected typo in `insert_at_beginning` method name

#### 🌐 Provider-Specific Fixes
- **fix**: Cerebras structured outputs for complex types
- **fix**: JSON schema errors in Cerebras provider
- **fix**: Missing future annotations in Cerebras generation provider
- **fix**: Langfuse OTEL client cost field names to match v3 specification
- **fix**: Wrong module level import in html.py
- **fix**: Removed deprecated modules

#### 🔄 Generation & Streaming
- **fix**: Empty choices handling in `get_tool_calls`
- **fix**: MCP protocol version updates and JSON-RPC compliance
- **fix**: Proper endpoint path handling with trailing slash

### 🔄 Refactoring & Improvements

#### 🏗️ Architecture
- **refactor**: Enhanced type parsing and schema generation for Google tool adapter
- **refactor**: Simplified choice building logic in Google adapter
- **refactor**: Improved message handling and type safety across providers
- **refactor**: Better conversation handling using conversation store
- **refactor**: Simplified tool execution results handling

#### 📝 Code Quality
- **refactor**: Used Sequence instead of list for better type hints
- **refactor**: Improved streaming agent examples with better typing
- **refactor**: Enhanced WhatsApp provider as ABC for BaseModel compatibility
- **refactor**: Changed Agent ID to string for increased flexibility
- **refactor**: Simplified examples by removing unused imports

#### 🔧 Developer Experience
- **chore**: Replaced async_lru with aiocache for better caching performance
- **chore**: Updated dependencies and improved project structure
- **chore**: Enhanced documentation and examples

### 📊 Performance & Monitoring
- Integrated performance metrics for better agent monitoring
- OpenTelemetry support for distributed tracing
- Improved caching mechanisms with aiocache
- Enhanced error handling and logging throughout the system

---

*This release represents a significant evolution of the agentle framework, bringing enhanced reliability, better developer experience, and powerful new features for building sophisticated AI agents.*

## v0.7.41
refactor(tools): improve type safety with ParamSpec and TypeVar

Update Tool class to use ParamSpec for parameter types and TypeVar for return types, enabling better type safety and callback support. Simplify documentation and remove redundant examples while preserving core functionality.

The changes include:
- Using ParamSpec to capture function parameter types
- Adding TypeVar for return type preservation
- Improving before_call/after_call callback typing
- Updating call and call_async methods to use proper type signatures
- Simplifying documentation to focus on type-safe usage

refactor(tools): simplify tool call interface by removing context param

## v0.7.40
fix(mcp): update protocol version and fix json-rpc compliance

- Update protocol version to "2025-06-18"
- Fix notification method name to "notifications/initialized"
- Add proper endpoint path handling with trailing slash
- Improve error handling and logging
- Ensure proper parameter handling for requests

## v0.7.39
fix(generation): handle empty choices in get_tool_calls

Add check for empty choices array to prevent index error and return empty list with warning

refactor(generations): simplify choice building logic in google adapter

Unify streaming and non-streaming choice building into a single method
Remove redundant code and improve handling of accumulated text
Ensure consistent behavior for all input cases

fix(langfuse_otel_client): update cost field names to match langfuse v3 spec

Change field names from 'total_cost', 'input_cost', 'output_cost' to 'total', 'input', 'output' to align with Langfuse V3 API requirements

## v0.7.38
fix(agent): remove redundant message appends and inline tool generation messages

Prevent duplicate message appends by removing separate append operations and directly including tool generation messages in the context when streaming. This maintains message history consistency and avoids potential race conditions.

## v0.7.37
feat(streaming): accumulate text chunks for streaming responses

Add _build_choices_with_accumulated_text method to properly accumulate text parts during streaming responses. This ensures complete text is available for each chunk rather than just the latest portion.

## v0.7.36
fix(agents): ensure tool results immediately follow tool calls

Fix message history sequence by moving tool results to immediately follow their corresponding tool calls. Add synthetic results for missing calls and clean up orphaned messages. This ensures proper message ordering required for agent execution.

feat(agent): add synchronous streaming support to agent.run

Implement synchronous streaming by bridging async iterator with a queue and background thread. This allows synchronous contexts to consume streaming responses without blocking.

Add example script demonstrating streaming usage with poem generation.

refactor(google-generation): make stream_async method synchronous and update return types

Change stream_async method to be synchronous and update return type annotations to AsyncGenerator for better clarity. Remove explicit return type annotation from implementation to match the overload signatures.

## v0.7.35
refactor(agent): simplify streaming agent example by removing unused imports

remove unnecessary type casting and imports in streaming agent example

refactor(streaming_agent): improve streaming output handling and typing

Add proper typing imports and cast for stream iterator
Replace pprint with direct text output handling for streaming chunks
Add visual separators and status messages for better user feedback

feat(example): add streaming agent example demonstrating async usage

Add a new example file showing how to use the Agent class with async streaming capabilities. The example includes a simple async function and demonstrates streaming output with pretty printing.

## v0.7.34
feat(api): add json schema support for endpoint parameters

implement from_json_schema method to create EndpointParameter from JSON schema
add _convert_json_schema helper to handle schema conversion
support object, array and primitive types with $ref resolution

## v0.7.33
feat(context): add replace_message_history method to Context class

refactor(agent): improve conversation history handling with replace_message_history
Add support for keeping developer messages when replacing history and ensure proper message persistence in conversation store.

refactor(google-tool-adapter): enhance type parsing and schema generation
Add comprehensive type parser for complex Python type annotations and improve JSON Schema conversion with better handling of unions, optionals, and nested structures.

chore(examples): simplify open_memory.py by removing unused imports and server setup

feat(agent): improve serialization and add endpoint support

- Replace async_lru with aiocache for better caching
- Add endpoint configuration support in Agent class
- Refactor serialization to use versioned dictionary format (experimental || WIP)
- Update dependencies to include aiocache

## v0.7.32

feat(agent): improve tool call tracking and message history handling

- Replace called_tools with all_tool_suggestions and all_tool_results for better tracking across iterations
- Modify message history handling to ensure all tool suggestions and results are properly included
- Add append_tool_calls method to generation model for final response consolidation

## v0.7.31

refactor(agent): simplify tool execution results handling in message history

Improve message history handling by directly adding tool execution results to the last user message instead of complex multi-step processing. This makes the code more straightforward and reduces edge cases while maintaining the same functionality.

## v0.7.30

feat(agent): add change_instructions method to modify agent instructions

## v0.7.29
- feat(agent): add methods to modify agent properties

Add change_name, change_apis and change_endpoints methods to allow dynamic modification of agent properties

## v0.7.28

- feat(agent): add append_instructions method and improve tool execution handling

- Implement append_instructions to allow dynamic instruction updates
- Enhance tool execution flow by properly handling tool results in message history
