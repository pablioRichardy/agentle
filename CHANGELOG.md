# Changelog

## v0.8.40

- feat(embedding_provider): add batch embedding generation methods for async processing

feat(google_embedding_provider): implement Google's native batch API for embeddings

feat(file_parser): introduce max_concurrent_provider_tasks for API call concurrency

fix(pdf): enhance thread safety with asyncio locks for image processing

fix(qdrant_vector_store): add wait parameter for async operations

refactor(vector_store): optimize upsert_file_async to use batch embedding generation

chore(docker): rename qdrant service to qdrant-api for clarity
