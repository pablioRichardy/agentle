# Changelog

## v0.7.11
fix(google): resolve function calling 400 error by using ToolExecutionResult

- Fix "Please ensure that the number of function response parts is equal 
  to the number of function call parts" Google API error
- Replace text-based tool result descriptions with ToolExecutionResult objects
- Maintain existing anti-repetition logic and warnings for better context
- Ensures 1:1 mapping between function_call and function_response parts
- Preserves all existing functionality while fixing Google API compliance

Fixes function calling with Google's Generative AI models by properly 
formatting tool execution results as structured function_response parts 
instead of unstructured text descriptions.

## v0.7.10

- feat: new `with_overrides` in `WhatsAppBotConfig` class to allow creation with only changing certain parameters of it.

- fix: more complex structured output types to `CerebrasGenerationProvider` provider are now properlly propagated to the API.



