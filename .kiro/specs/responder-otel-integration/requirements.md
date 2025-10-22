# Requirements Document

## Introduction

This feature adds OpenTelemetry (OTel) observability integration to the `Responder` class in Agentle. The integration will enable tracing, metrics collection, and cost tracking for API calls made through the Responder, similar to how the `GenerationProvider` class implements observability through the `@observe` decorator. However, this implementation will be done directly within the class methods rather than using a decorator pattern.

## Glossary

- **Responder**: The Agentle class responsible for making API calls to OpenRouter/OpenAI Responses API
- **OtelClient**: Abstract interface for OpenTelemetry clients that handle tracing and observability
- **Trace Context**: A context object that tracks a complete operation from start to finish
- **Generation Context**: A context object that tracks a specific AI model invocation
- **Response API**: OpenRouter/OpenAI's Responses API for structured AI interactions
- **Structured Output**: Parsed Pydantic model output from AI responses
- **Streaming Response**: Server-sent events (SSE) based response delivery
- **Non-streaming Response**: Single HTTP response with complete data

## Requirements

### Requirement 1

**User Story:** As a developer using Agentle, I want the Responder class to automatically trace all API calls, so that I can monitor performance, costs, and errors in my observability platform.

#### Acceptance Criteria

1. WHEN a Responder instance is created with otel_clients, THE Responder SHALL store the clients for use in tracing operations
2. WHEN respond_async is called, THE Responder SHALL create trace and generation contexts for each configured OtelClient
3. WHEN an API call completes successfully, THE Responder SHALL update the trace and generation contexts with response data, usage metrics, and cost information
4. WHEN an API call fails, THE Responder SHALL record the error in the trace and generation contexts
5. WHERE multiple OtelClients are configured, THE Responder SHALL send telemetry data to all clients without blocking the main execution

### Requirement 2

**User Story:** As a developer, I want cost and usage metrics automatically calculated and tracked, so that I can monitor the financial impact of my API usage.

#### Acceptance Criteria

1. WHEN a non-streaming response is received, THE Responder SHALL extract token usage from the response
2. WHEN token usage is available, THE Responder SHALL calculate input and output costs based on the model pricing
3. WHEN costs are calculated, THE Responder SHALL include them in the trace metadata with currency information
4. WHEN usage details are available, THE Responder SHALL include token counts in the generation context
5. THE Responder SHALL handle missing usage data gracefully without failing the request

### Requirement 3

**User Story:** As a developer, I want streaming responses to be traced with accumulated metrics, so that I can observe the complete interaction even when data arrives incrementally.

#### Acceptance Criteria

1. WHEN streaming is enabled, THE Responder SHALL create trace and generation contexts before streaming begins
2. WHILE streaming events are processed, THE Responder SHALL accumulate text content for structured output parsing
3. WHEN a response.completed event is received, THE Responder SHALL update contexts with final metrics and parsed output
4. WHEN streaming fails, THE Responder SHALL record the error with accumulated data up to the failure point
5. THE Responder SHALL ensure contexts are properly closed after streaming completes or fails

### Requirement 4

**User Story:** As a developer, I want the tracing implementation to be non-blocking and resilient, so that observability failures don't impact my application's core functionality.

#### Acceptance Criteria

1. WHEN an OtelClient operation fails, THE Responder SHALL log the error and continue execution
2. WHEN multiple OtelClients are configured, THE Responder SHALL process each client independently
3. IF one OtelClient fails, THEN THE Responder SHALL continue processing remaining clients
4. THE Responder SHALL use fire-and-forget patterns for non-critical telemetry operations
5. THE Responder SHALL ensure all contexts are cleaned up even when errors occur

### Requirement 5

**User Story:** As a developer, I want detailed metadata captured in traces, so that I can debug issues and understand the context of each API call.

#### Acceptance Criteria

1. WHEN creating a trace context, THE Responder SHALL include model name, provider, and request parameters
2. WHEN a response includes structured output, THE Responder SHALL include the parsed data in trace metadata
3. WHEN reasoning is used, THE Responder SHALL track reasoning tokens separately from output tokens
4. WHEN tool calls are made, THE Responder SHALL include tool usage information in the trace
5. THE Responder SHALL include request and response timestamps for latency calculation

### Requirement 6

**User Story:** As a developer, I want consistent tracing behavior between streaming and non-streaming modes, so that I can analyze both types of requests uniformly.

#### Acceptance Criteria

1. THE Responder SHALL use the same trace structure for streaming and non-streaming requests
2. THE Responder SHALL calculate the same metrics (cost, usage, latency) for both modes
3. THE Responder SHALL handle structured output parsing consistently in both modes
4. THE Responder SHALL apply the same error handling patterns in both modes
5. THE Responder SHALL ensure trace metadata format is identical regardless of streaming mode
