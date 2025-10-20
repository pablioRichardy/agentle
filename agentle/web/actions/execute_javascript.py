from __future__ import annotations
from typing import TYPE_CHECKING, Literal
from rsb.models import BaseModel, Field

if TYPE_CHECKING:
    from playwright.async_api import Page


class ExecuteJavascript(BaseModel):
    type: Literal["execute_javascript"] = Field(
        default="execute_javascript",
        description="Execute a JavaScript code on the current page.",
    )

    script: str = Field(
        ...,
        description="The JavaScript code to execute.",
        examples=["document.querySelector('.button').click();"],
    )

    async def execute(self, page: Page) -> None: ...
