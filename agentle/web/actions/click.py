from __future__ import annotations
from typing import TYPE_CHECKING, Literal
from rsb.models import BaseModel, Field

if TYPE_CHECKING:
    from playwright.async_api import Page


class Click(BaseModel):
    type: Literal["click"] = Field(default="click")
    selector: str = Field(
        ...,
        description="Query selector to find the element by",
        examples=["#load-more-button"],
    )
    all: bool = Field(
        default=False,
        description="Clicks all elements matched by the selector, not just the first one. Does not throw an error if no elements match the selector.",
    )

    async def execute(self, page: Page) -> None: ...
