import abc
from collections.abc import MutableSequence, Sequence

from rsb.coroutines.run_sync import run_sync

from agentle.embeddings.models.embed_content import EmbedContent
from agentle.embeddings.models.embedding import Embedding
from agentle.embeddings.providers.embedding_provider import EmbeddingProvider
from agentle.generations.providers.base.generation_provider import GenerationProvider
from agentle.generations.tools.tool import Tool
from agentle.parsing.chunk import Chunk
from agentle.parsing.chunking.chunking_config import ChunkingConfig
from agentle.parsing.chunking.chunking_strategy import ChunkingStrategy
from agentle.parsing.parsed_file import ParsedFile
from agentle.vector_stores.create_collection_config import CreateCollectionConfig
from agentle.vector_stores.upserted_file import UpsertedFile


class VectorStore(abc.ABC):
    default_collection_name: str
    embedding_provider: EmbeddingProvider
    generation_provider: GenerationProvider | None

    def __init__(
        self,
        *,
        default_collection_name: str = "agentle",
        embedding_provider: EmbeddingProvider,
        generation_provider: GenerationProvider | None,
    ) -> None:
        self.default_collection_name = default_collection_name
        self.embedding_provider = embedding_provider
        self.generation_provider = generation_provider

    async def find_related_content(
        self,
        query: str | Embedding | Sequence[float],
        *,
        k: int = 10,
        collection_name: str | None = None,
    ) -> Sequence[Chunk]:
        match query:
            case str():
                embedding = await self.embedding_provider.generate_embeddings_async(
                    contents=query
                )

                return await self._find_related_content(
                    query=embedding.embeddings.value,
                    k=k,
                    collection_name=collection_name,
                )
            case Embedding():
                return await self._find_related_content(
                    query=query.value, k=k, collection_name=collection_name
                )
            case Sequence():
                return await self._find_related_content(
                    query=query,
                    k=k,
                    collection_name=collection_name,
                )

    @abc.abstractmethod
    async def _find_related_content(
        self, query: Sequence[float], *, k: int = 10, collection_name: str | None = None
    ) -> Sequence[Chunk]: ...

    async def upsert(
        self,
        points: Embedding | Sequence[float],
        *,
        timeout: float | None = None,
        collection_name: str | None = None,
    ) -> None:
        return run_sync(
            self.upsert_async,
            points=points,
            timeout=timeout,
            collection_name=collection_name,
        )

    @abc.abstractmethod
    async def upsert_async(
        self,
        points: Embedding | Sequence[float],
        *,
        collection_name: str | None = None,
    ) -> None:
        if len(points) == 0:
            return None

        if isinstance(points, Sequence):
            return await self._upsert_async(
                points=Embedding(value=points),
                collection_name=collection_name,
            )

        return await self._upsert_async(
            points=points,
            collection_name=collection_name,
        )

    @abc.abstractmethod
    async def _upsert_async(
        self,
        points: Embedding,
        *,
        collection_name: str | None = None,
    ) -> None: ...

    def upsert_file(
        self,
        file: ParsedFile,
        *,
        timeout: float | None = None,
        chunking_strategy: ChunkingStrategy,
        chunking_config: ChunkingConfig,
        collection_name: str | None,
    ) -> UpsertedFile:
        return run_sync(
            self.upsert_file_async,
            file=file,
            timeout=timeout,
            chunking_strategy=chunking_strategy,
            chunking_config=chunking_config,
            collection_name=collection_name,
        )

    async def upsert_file_async(
        self,
        file: ParsedFile,
        *,
        chunking_strategy: ChunkingStrategy,
        chunking_config: ChunkingConfig,
        collection_name: str | None,
    ) -> UpsertedFile:
        chunks: Sequence[Chunk] = await file.chunkify_async(
            strategy=chunking_strategy, config=chunking_config
        )

        embed_contents: Sequence[EmbedContent] = [
            await self.embedding_provider.generate_embeddings_async(
                c.text, metadata=c.metadata
            )
            for c in chunks
        ]

        ids: MutableSequence[str] = []

        for e in embed_contents:
            await self.upsert_async(
                points=e.embeddings,
                collection_name=collection_name,
            )

            ids.append(e.embeddings.id)

        return UpsertedFile(chunk_ids=ids)

    @abc.abstractmethod
    async def create_collection_async(
        self, collection_name: str, *, config: CreateCollectionConfig
    ) -> None: ...

    def as_search_tool(self) -> Tool[Sequence[Chunk]]:
        async def search_async(query: str, *, top_k: int = 3) -> Sequence[Chunk]:
            return await self.find_related_content(query=query, k=top_k)

        return Tool.from_callable(search_async)
