"""
Concrete implementation of AsyncStream for streaming responses.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import AsyncContextManager, cast

from agentle.responses.definitions.response_completed_event import (
    ResponseCompletedEvent,
)


class AsyncStream[_T, TextFormatT = None](
    AsyncIterator[_T], AsyncContextManager["AsyncStream[_T, TextFormatT]"]
):
    """
    Concrete implementation of AsyncStream protocol.

    Wraps an async generator to provide both AsyncIterator and AsyncContextManager
    interfaces for streaming responses.

    Usage:
        ```python
        async def generate_events():
            for i in range(10):
                yield i

        stream = AsyncStreamImpl(generate_events())

        # Use as async iterator
        async for event in stream:
            print(event)

        # Or use as context manager
        async with stream:
            async for event in stream:
                print(event)
        ```
    """

    def __init__(
        self, generator: AsyncIterator[_T], text_format: type[TextFormatT] | None = None
    ):
        """
        Initialize the stream with an async generator.

        Args:
            generator: The async generator that produces stream items
        """
        self._generator = generator
        self._closed = False
        self._final_event: _T | None = None
        self._text_format = text_format

    async def __anext__(self) -> _T:
        """
        Get the next item from the stream.

        Returns:
            The next item from the underlying generator

        Raises:
            StopAsyncIteration: When the stream is exhausted
        """
        if self._closed:
            raise StopAsyncIteration

        try:
            event = await self._generator.__anext__()
            # Store the final event (typically ResponseCompletedEvent)
            self._final_event = event
            return event
        except StopAsyncIteration:
            self._closed = True
            raise

    def __aiter__(self) -> AsyncStream[_T, TextFormatT]:
        """
        Return self as the async iterator.

        Returns:
            Self
        """
        return self

    async def __aenter__(self) -> AsyncStream[_T, TextFormatT]:
        """
        Enter the async context manager.

        Returns:
            Self
        """
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: object | None,
    ) -> None:
        """
        Exit the async context manager.

        Performs cleanup by closing the underlying generator if it supports it.

        Args:
            exc_type: Exception type if an exception occurred
            exc_val: Exception value if an exception occurred
            exc_tb: Exception traceback if an exception occurred
        """
        self._closed = True

        # Try to close the generator if it has aclose method
        if hasattr(self._generator, "aclose"):
            await self._generator.aclose()  # type: ignore

    @property
    def output_parsed(self) -> TextFormatT:
        """Extract parsed output from the final ResponseCompletedEvent if available."""
        if self._final_event and isinstance(self._final_event, ResponseCompletedEvent):
            result = self._final_event.response.output_parsed
            if result is None and self._text_format:
                raise ValueError("No parsed output available")

            return cast(TextFormatT, result)

        return cast(TextFormatT, None)
