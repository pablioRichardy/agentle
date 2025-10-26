"""Circuit breaker for resilient API calls.

This module adapts the resilience module's circuit breaker implementations
for use in the APIs module, maintaining backward compatibility.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from agentle.agents.apis.circuit_breaker_error import CircuitBreakerError
from agentle.agents.apis.request_config import RequestConfig
from agentle.resilience.circuit_breaker.in_memory_circuit_breaker import (
    InMemoryCircuitBreaker,
)


class CircuitBreaker:
    """
    Circuit breaker implementation for resilient API calls.

    This wraps the resilience module's InMemoryCircuitBreaker to provide
    a simpler call-based API for endpoint usage.
    """

    def __init__(self, config: RequestConfig):
        self.config = config
        self._circuit_id = "default"  # Single circuit per endpoint
        # Initialize the underlying circuit breaker from resilience module
        self._impl = InMemoryCircuitBreaker(
            failure_threshold=config.circuit_breaker_failure_threshold,
            recovery_timeout=config.circuit_breaker_recovery_timeout,
            half_open_success_threshold=config.circuit_breaker_success_threshold,
            enable_metrics=config.enable_metrics,
        )

    async def call(self, func: Callable[[], Any]) -> Any:
        """
        Execute function with circuit breaker protection.

        Args:
            func: Async function to execute

        Returns:
            Result of func call

        Raises:
            CircuitBreakerError: If circuit is open
        """
        # Check if circuit is open
        if await self._impl.is_open(self._circuit_id):
            # Get circuit state for more details
            state = await self._impl.get_circuit_state(self._circuit_id)
            next_retry_seconds = state.get("next_recovery_attempt_in_seconds", 0)

            if next_retry_seconds > 0:
                raise CircuitBreakerError(
                    f"Circuit breaker is OPEN. Retry after {next_retry_seconds:.1f}s"
                )

        # Execute the function
        try:
            result = await func()
            await self._impl.record_success(self._circuit_id)
            return result
        except Exception:
            await self._impl.record_failure(self._circuit_id)
            raise
