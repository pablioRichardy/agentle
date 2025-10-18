from typing import override

# import aiohttp

from agentle.responses._streaming.async_stream import AsyncStream

from agentle.responses.definitions.create_response import CreateResponse

from agentle.responses.definitions.response import Response
from agentle.responses.definitions.response_stream_event import ResponseStreamEvent
from agentle.responses.responder_mixin import ResponderMixin


# TODO(arthur): implement one subclass for now
class OpenRouterResponder(ResponderMixin):
    @override
    async def _respond_async[TextFormatT](
        self, create_response: CreateResponse[TextFormatT]
    ) -> Response[TextFormatT] | AsyncStream[ResponseStreamEvent]: ...
