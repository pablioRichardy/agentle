# Changelog

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
