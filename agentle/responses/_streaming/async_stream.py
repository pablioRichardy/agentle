from __future__ import annotations

from collections.abc import AsyncIterator
from typing import AsyncContextManager


class AsyncStream[_T, TextFormatT = None](
    AsyncIterator[_T], AsyncContextManager["AsyncStream[_T, TextFormatT]"]
):
    @property
    def output_parsed(self) -> TextFormatT:
        raise NotImplementedError
