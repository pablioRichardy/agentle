from __future__ import annotations

from pydantic import BaseModel

from agentle.responses.definitions.create_response import CreateResponse


class CreateChatCompletion(BaseModel):
    @classmethod
    def from_create_response(
        cls, create_response: CreateResponse
    ) -> CreateChatCompletion: ...
