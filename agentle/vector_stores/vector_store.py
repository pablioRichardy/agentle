import abc
from collections.abc import Sequence

from rsb.coroutines.run_sync import run_sync

from agentle.embeddings.models.embeddings import Embeddings
from agentle.embeddings.providers.embedding_provider import EmbeddingProvider
from agentle.parsing.parsed_file import ParsedFile
from agentle.vector_stores.ingestion_result import IngestionResult


class VectorStore(abc.ABC):
    embedding_provider: EmbeddingProvider | None

    async def upsert(self, points: Sequence[Embeddings]) -> IngestionResult:
        return run_sync(self.upsert_async, points=points)

    @abc.abstractmethod
    async def upsert_async(self, points: Sequence[Embeddings]) -> IngestionResult: ...

    def upsert_file(self, file: ParsedFile) -> IngestionResult: ...

    def upsert_file_async(self, file: ParsedFile) -> IngestionResult: ...
