from __future__ import annotations
from typing import TYPE_CHECKING, Literal
from rsb.models import BaseModel, Field


if TYPE_CHECKING:
    from playwright.async_api import Page


class PressAKey(BaseModel):
    type: Literal["press"] = Field(
        default="press", description="Press a key on the keyboard."
    )
    key: str = Field(
        ...,
        description="The key to press.",
        examples=["Enter", "Space", "ArrowUp", "ArrowDown", "ArrowLeft", "ArrowRight"],
    )

    async def execute(self, page: Page) -> None:
        await page.keyboard.press(self.key)
