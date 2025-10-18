
from __future__ import annotations

from collections.abc import AsyncIterator
from typing import AsyncContextManager


class AsyncStream[_T](AsyncIterator[_T], AsyncContextManager["AsyncStream[_T]"]): ...
