from __future__ import annotations
from typing import TYPE_CHECKING, Literal
from rsb.models import BaseModel, Field


if TYPE_CHECKING:
    from playwright.async_api import Page


class Scrape(BaseModel):
    type: Literal["scrape"] = Field(
        default="scrape",
        description="Scrape the current page content, returns the url and the html.",
    )

    async def execute(self, page: Page) -> None: ...
