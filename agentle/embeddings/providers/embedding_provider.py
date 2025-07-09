import abc
from typing import Protocol

from agentle.embeddings.models.embed_content import EmbedContent


class EmbeddingProvider(Protocol):
    @abc.abstractmethod
    async def generate_embeddings_async(self, contents: str) -> EmbedContent: ...
