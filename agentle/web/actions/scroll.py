from __future__ import annotations
from typing import TYPE_CHECKING, Literal
from rsb.models import BaseModel, Field


if TYPE_CHECKING:
    from playwright.async_api import Page


class Scroll(BaseModel):
    type: Literal["scroll"] = Field(
        default="scroll", description="Scroll the page or a specific element."
    )

    direction: Literal["up", "down", "left", "right"] = Field(
        default="down",
        description="The direction to scroll.",
        examples=["up", "down", "left", "right"],
    )

    amount: int = Field(
        default=100,
        description="The amount to scroll in pixels.",
        ge=0,
        le=1000,
        examples=[100, 200, 300, 400, 500, 600, 700, 800, 900, 1000],
    )

    selector: str = Field(
        ...,
        description="Query selector for the element to scroll.",
        examples=["#load-more-button"],
    )

    async def execute(self, page: Page) -> None:
        # Determine scroll delta based on direction
        delta_x = 0
        delta_y = 0

        if self.direction == "down":
            delta_y = self.amount
        elif self.direction == "up":
            delta_y = -self.amount
        elif self.direction == "right":
            delta_x = self.amount
        elif self.direction == "left":
            delta_x = -self.amount

        # Scroll the element
        await page.evaluate(
            """
            (args) => {
                const element = document.querySelector(args.selector);
                if (element) {
                    element.scrollBy(args.deltaX, args.deltaY);
                }
            }
            """,
            {"selector": self.selector, "deltaX": delta_x, "deltaY": delta_y},
        )
