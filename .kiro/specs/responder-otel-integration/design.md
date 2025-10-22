# Design Document

## Overview

This design document outlines the integration of OpenTelemetry (OTel) observability into the `Responder` class. Unlike the `GenerationProvider` which uses the `@observe` decorator, the `Responder` will implement tracing directly within its methods. This approach provides more granular control over the tracing lifecycle and better handles the dual nature of streaming vs non-streaming responses.

The implementation will follow these key principles:
- **Non-invasive**: Tracing logic won't interfere with core API functionality
- **Resilient**: Telemetry failures won't break API calls
- **Efficient**: Use fire-and-forget patterns for non-critical operations
- **Consistent**: Same tracing structure for streaming and non-streaming modes

## Architecture

### High-Level Flow

```
┌─────────────────────────────────────────────────────────────┐
│                      Responder.respond_async                 │
│                                                              │
│  1. Validate inputs & prepare request                       │
│  2. Initialize tracing contexts (if otel_clients present)   │
│  3. Make API call                                           │
│  4. Process response (streaming or non-streaming)           │
│  5. Update tracing contexts with results                    │
│  6. Cleanup contexts                                        │
└─────────────────────────────────────────────────────────────┘
```

### Component Interaction

```
┌──────────────┐         ┌──────────────┐         ┌──────────────┐
│   Responder  │────────▶│ OtelClient 1 │         │ OtelClient N │
│              │         │  (Langfuse)  │   ...   │   (Custom)   │
│              │◀────────│              │         │              │
└──────────────┘         └──────────────┘         └──────────────┘
       │
       │ API Calls
       ▼
┌──────────────────────────────────────┐
│  OpenRouter / OpenAI Responses API   │
└──────────────────────────────────────┘
```

## Components and Interfaces

### 1. Responder Class Enhancement

The `Responder` class will be enhanced with:

**New Attributes:**
- `otel_clients: Sequence[OtelClientType]` - Already exists, will be utilized

**New Private Methods:**

```python
async def _create_tracing_contexts(
    self,
    *,
    model: str,
    request_payload: dict[str, Any],
    generation_config: dict[str, Any],
) -> list[dict[str, Any]]:
    """
    Create trace and generation contexts for all configured OtelClients.
    
    Returns a list of context dictionaries containing:
    - client: The OtelClient instance
    - trace_gen: The trace context generator
    - trace_ctx: The trace context object
    - generation_gen: The generation context generator
    - generation_ctx: The generation context object
    """
```

```python
async def _update_tracing_success(
    self,
    *,
    active_contexts: list[dict[str, Any]],
    response: Response[Any] | None = None,
    accumulated_text: str = "",
    start_time: datetime,
    model: str,
    text_format: Type[Any] | None = None,
) -> None:
    """
    Update all tracing contexts with successful response data.
    
    Extracts and calculates:
    - Token usage (input, output, total)
    - Cost metrics (input cost, output cost, total cost)
    - Latency
    - Structured output (if applicable)
    """
```

```python
async def _update_tracing_error(
    self,
    *,
    active_contexts: list[dict[str, Any]],
    error: Exception,
    start_time: datetime,
    metadata: dict[str, Any],
) -> None:
    """
    Update all tracing contexts with error information.
    """
```

```python
async def _cleanup_tracing_contexts(
    self,
    active_contexts: list[dict[str, Any]],
) -> None:
    """
    Cleanup all tracing contexts by closing generators.
    """
```

```python
def _extract_usage_from_response(
    self,
    response: Response[Any],
) -> dict[str, Any] | None:
    """
    Extract token usage information from a Response object.
    
    Returns:
    {
        "input": int,
        "output": int,
        "total": int,
        "unit": "TOKENS"
    }
    """
```

```python
async def _calculate_costs(
    self,
    *,
    model: str,
    input_tokens: int,
    output_tokens: int,
) -> dict[str, Any] | None:
    """
    Calculate cost metrics based on token usage.
    
    Note: This requires implementing a pricing lookup mechanism
    similar to GenerationProvider's price_per_million_tokens methods.
    
    Returns:
    {
        "input": float,
        "output": float,
        "total": float,
        "currency": "USD"
    }
    """
```

```python
def _prepare_trace_input_data(
    self,
    request_payload: dict[str, Any],
) -> dict[str, Any]:
    """
    Prepare input data for trace context from request payload.
    
    Extracts relevant fields like:
    - input/messages
    - model
    - tools
    - reasoning settings
    - temperature, top_p, etc.
    """
```

```python
def _prepare_trace_metadata(
    self,
    *,
    model: str,
    base_url: str,
    generation_config: dict[str, Any],
) -> dict[str, Any]:
    """
    Prepare metadata for trace context.
    
    Includes:
    - model name
    - provider (openrouter/openai)
    - base_url
    - custom metadata from generation_config
    """
```

### 2. Integration Points

#### A. Non-Streaming Response Flow

```python
async def _respond_async(...):
    # 1. Setup
    start_time = datetime.now()
    active_contexts = []
    
    try:
        # 2. Create tracing contexts
        if self.otel_clients:
            active_contexts = await self._create_tracing_contexts(
                model=model,
                request_payload=request_payload,
                generation_config=generation_config,
            )
        
        # 3. Make API call
        async with session.post(...) as response:
            if is_streaming:
                # Handle streaming (see below)
            else:
                # 4. Parse response
                parsed_response = await self._handle_non_streaming_response(...)
                
                # 5. Update tracing with success
                if active_contexts:
                    await self._update_tracing_success(
                        active_contexts=active_contexts,
                        response=parsed_response,
                        start_time=start_time,
                        model=model,
                        text_format=text_format,
                    )
                
                return parsed_response
    
    except Exception as e:
        # 6. Update tracing with error
        if active_contexts:
            await self._update_tracing_error(
                active_contexts=active_contexts,
                error=e,
                start_time=start_time,
                metadata=trace_metadata,
            )
        raise
    
    finally:
        # 7. Cleanup
        if active_contexts:
            await self._cleanup_tracing_contexts(active_contexts)
```

#### B. Streaming Response Flow

For streaming, we need to wrap the event generator to update tracing on completion:

```python
async def _stream_events_with_tracing(
    self,
    content_lines: list[bytes],
    text_format: Type[Any] | None,
    active_contexts: list[dict[str, Any]],
    start_time: datetime,
    model: str,
) -> AsyncIterator[ResponseStreamEvent]:
    """
    Stream events and update tracing on completion.
    """
    accumulated_text = ""
    final_event = None
    
    try:
        async for event in self._stream_events_from_buffer(content_lines, text_format):
            # Accumulate text for metrics
            if hasattr(event, 'delta'):
                accumulated_text += getattr(event, 'delta', '')
            
            # Track final event
            if isinstance(event, ResponseCompletedEvent):
                final_event = event
            
            yield event
        
        # Update tracing with success
        if active_contexts and final_event:
            await self._update_tracing_success(
                active_contexts=active_contexts,
                response=final_event.response,
                accumulated_text=accumulated_text,
                start_time=start_time,
                model=model,
                text_format=text_format,
            )
    
    except Exception as e:
        # Update tracing with error
        if active_contexts:
            await self._update_tracing_error(
                active_contexts=active_contexts,
                error=e,
                start_time=start_time,
                metadata={},
            )
        raise
```

### 3. Pricing Integration

Since the Responder needs to calculate costs, we need a pricing lookup mechanism. Options:

**Option A: Static Pricing Dictionary**
```python
MODEL_PRICING = {
    "gpt-4": {"input": 30.0, "output": 60.0},
    "gpt-3.5-turbo": {"input": 0.5, "output": 1.5},
    # ... more models
}
```

**Option B: Pricing Service (Recommended)**
```python
class PricingService:
    """Service for looking up model pricing."""
    
    async def get_input_price_per_million(self, model: str) -> float:
        """Get input token price per million tokens."""
        
    async def get_output_price_per_million(self, model: str) -> float:
        """Get output token price per million tokens."""
```

**Decision**: Use Option B with a default implementation that can be overridden. The Responder will have an optional `pricing_service` attribute.

## Data Models

### Trace Input Data Structure

```python
{
    "input": str | list[dict],  # The input/messages
    "model": str,
    "has_tools": bool,
    "tools_count": int,
    "has_structured_output": bool,
    "reasoning_enabled": bool,
    "reasoning_effort": str | None,
    "temperature": float | None,
    "top_p": float | None,
    "max_output_tokens": int | None,
    "stream": bool,
}
```

### Trace Metadata Structure

```python
{
    "model": str,
    "provider": str,  # "openrouter" or "openai"
    "base_url": str,
    "api_version": str,
    # Custom metadata from user
    **custom_metadata
}
```

### Usage Details Structure

```python
{
    "input": int,  # prompt tokens
    "output": int,  # completion tokens
    "total": int,
    "unit": "TOKENS",
    "reasoning_tokens": int | None,  # if available
}
```

### Cost Details Structure

```python
{
    "input": float,  # cost in USD
    "output": float,
    "total": float,
    "currency": "USD",
    "input_tokens": int,
    "output_tokens": int,
}
```

## Error Handling

### Error Categories

1. **Tracing Setup Errors**: Failures during context creation
   - Log error, continue without tracing
   - Don't fail the API call

2. **API Call Errors**: Failures from OpenRouter/OpenAI
   - Record in tracing contexts
   - Re-raise to caller

3. **Tracing Update Errors**: Failures during context updates
   - Log error, continue
   - Use fire-and-forget for non-critical updates

4. **Cleanup Errors**: Failures during context cleanup
   - Log error, don't re-raise
   - Ensure all contexts are attempted

### Error Handling Pattern

```python
try:
    # Critical operation
    result = await api_call()
except Exception as e:
    # Record in tracing
    if active_contexts:
        try:
            await self._update_tracing_error(...)
        except Exception as trace_error:
            logger.error(f"Failed to record error in tracing: {trace_error}")
    # Re-raise original error
    raise
```

## Testing Strategy

### Unit Tests

1. **Context Creation Tests**
   - Test with no otel_clients
   - Test with single otel_client
   - Test with multiple otel_clients
   - Test context creation failure handling

2. **Usage Extraction Tests**
   - Test with complete usage data
   - Test with missing usage data
   - Test with reasoning tokens

3. **Cost Calculation Tests**
   - Test with known model pricing
   - Test with unknown model
   - Test with zero tokens

4. **Metadata Preparation Tests**
   - Test input data extraction
   - Test metadata extraction
   - Test custom metadata merging

### Integration Tests

1. **Non-Streaming Flow Tests**
   - Test successful response with tracing
   - Test error response with tracing
   - Test without otel_clients

2. **Streaming Flow Tests**
   - Test successful streaming with tracing
   - Test streaming error with tracing
   - Test accumulated metrics

3. **End-to-End Tests**
   - Test with real OtelClient (mock backend)
   - Test with multiple clients
   - Test resilience to tracing failures

## Performance Considerations

1. **Non-Blocking Operations**
   - Use fire-and-forget for score additions
   - Use fire-and-forget for non-critical updates

2. **Context Cleanup**
   - Always cleanup in finally block
   - Handle cleanup errors gracefully

3. **Memory Management**
   - Don't accumulate large text in memory for streaming
   - Use generators where possible

4. **Latency Impact**
   - Tracing setup: ~5-10ms overhead
   - Tracing updates: ~5-10ms overhead
   - Total overhead: ~10-20ms per request

## Migration Path

Since `otel_clients` is already an attribute of `Responder`, no breaking changes are needed. The integration will be:

1. **Backward Compatible**: Existing code without otel_clients continues to work
2. **Opt-In**: Tracing only happens when otel_clients are provided
3. **Gradual Adoption**: Users can add otel_clients to existing Responder instances

## Future Enhancements

1. **Automatic Pricing Updates**: Fetch pricing from external service
2. **Custom Metrics**: Allow users to add custom metrics to traces
3. **Sampling**: Implement trace sampling for high-volume scenarios
4. **Batch Updates**: Batch multiple trace updates for efficiency
5. **Trace Correlation**: Correlate Responder traces with GenerationProvider traces
