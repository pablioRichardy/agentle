from typing import Annotated
from agentle.responses.open_router import OpenRouterResponder
from pydantic import Discriminator

type Responder = Annotated[OpenRouterResponder, Discriminator("type")]
