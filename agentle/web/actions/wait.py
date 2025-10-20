from __future__ import annotations

from typing import TYPE_CHECKING, Literal

from rsb.models import BaseModel, Field

if TYPE_CHECKING:
    from playwright.async_api import Page


class Wait(BaseModel):
    type: Literal["wait"]
    milliseconds: int = Field(..., description="Number of milliseconds to wait")
    selector: str = Field(..., description="Query selector to find the element by")

    async def execute(self, page: Page) -> None: ...
