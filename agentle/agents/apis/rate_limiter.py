"""Rate limiter for API calls.

This module adapts the resilience module's rate limiter implementations
for use in the APIs module, maintaining backward compatibility.
"""

from __future__ import annotations

import asyncio

from agentle.agents.apis.request_config import RequestConfig
from agentle.resilience.rate_limiting.rate_limit_config import RateLimitConfig
from agentle.resilience.rate_limiting.in_memory_rate_limiter import (
    InMemoryRateLimiter as ResilienceRateLimiter,
)


class RateLimiter:
    """
    Rate limiter for API calls.

    This wraps the resilience module's InMemoryRateLimiter to provide
    a simpler acquire-based API for endpoint usage.
    """

    def __init__(self, config: RequestConfig):
        self.config = config
        self._identifier = "default"  # Single rate limit per endpoint

        # Convert rate limit config to resilience module format
        rate_limit_config: RateLimitConfig = {
            "max_requests_per_minute": int(
                config.rate_limit_calls * (60 / config.rate_limit_period)
            )
            if config.rate_limit_period <= 60
            else config.rate_limit_calls,
        }

        # Initialize the underlying rate limiter from resilience module
        self._impl = ResilienceRateLimiter(
            default_config=rate_limit_config,
            enable_metrics=config.enable_metrics,
        )

    async def acquire(self) -> None:
        """
        Acquire rate limit slot, waiting if necessary.

        This will block until a slot is available.
        """
        # Wait until we can proceed
        while not await self._impl.can_proceed(self._identifier):
            # Wait a short time before checking again
            await asyncio.sleep(0.1)

        # Record the request
        await self._impl.record_request(self._identifier)
