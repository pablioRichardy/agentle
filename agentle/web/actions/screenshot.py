from __future__ import annotations
from typing import TYPE_CHECKING, Literal

from rsb.models.base_model import BaseModel
from rsb.models.field import Field

from agentle.web.actions.viewport import Viewport


if TYPE_CHECKING:
    from playwright.async_api import Page


class Screenshot(BaseModel):
    type: Literal["screenshot"] = Field(
        default="screenshot",
        description="Capture a screenshot of the current page or a specific element.",
    )
    full_page: bool = Field(
        default=False,
        description="Whether to capture a full-page screenshot or limit to the current viewport.",
    )
    quality: int = Field(
        description="The quality of the screenshot, from 1 to 100. 100 is the highest quality.",
        ge=0,
        le=100,
    )
    viewport: Viewport | None = Field(default=None)

    async def execute(self, page: Page) -> bytes:
        if self.viewport:
            await page.set_viewport_size(
                {"width": self.viewport.width, "height": self.viewport.height}
            )

        screenshot_bytes = await page.screenshot(
            full_page=self.full_page,
            quality=self.quality,
            type="jpeg",
        )
        return screenshot_bytes
