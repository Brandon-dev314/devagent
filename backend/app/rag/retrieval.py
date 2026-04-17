import logging
import uuid
from qdrant_client import QdrantClient, AsyncQdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
    PointStruct,
    Filter,
    FieldCondition,
    MatchValue,
)

from app.config import settings
from app.models.schemas import DocumentChunk, SearchResult
from app.rag.embeddings import EMBEDDING_DIMENSIONS

logger = logging.getLogger("devagent.retrieval")


class RetrievalService:

    def __init__(
        self,
        host: str | None = None,
        port: int | None = None,
        collection_name: str | None = None,
    ):
        self.host = host or settings.qdrant_host
        self.port = port or settings.qdrant_port
        self.collection_name = collection_name or settings.qdrant_collection

        is_cloud = "cloud.qdrant.io" in self.host

        client_kwargs = {
            "host": self.host,
            "port": self.port,
            "https": is_cloud,
            "api_key": settings.qdrant_api_key if is_cloud else None,
            "timeout": 60,  
        }

        self.client = QdrantClient(**client_kwargs)
        self.async_client = AsyncQdrantClient(**client_kwargs)

    def ensure_collection(self) -> None:
        collections = self.client.get_collections().collections
        exists = any(c.name == self.collection_name for c in collections)

        if not exists:
            logger.info("Creating Qdrant collection '%s'...", self.collection_name)
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=EMBEDDING_DIMENSIONS,
                    distance=Distance.COSINE,
                ),
            )
            logger.info("Collection '%s' created", self.collection_name)
        else:
            logger.info("Collection '%s' already exists", self.collection_name)

    def upsert_chunks(self, chunks: list[DocumentChunk]) -> int:

        if not chunks:
            return 0

        points = []
        for chunk in chunks:
            if chunk.embedding is None:
                logger.warning("Chunk %s has no embedding, skipping", chunk.chunk_id)
                continue

            point_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, chunk.chunk_id))

            point = PointStruct(
                id=point_id,
                vector=chunk.embedding,
                payload={
                    "chunk_id": chunk.chunk_id,  
                    "text": chunk.text,
                    "chunk_index": chunk.chunk_index,
                    "source": chunk.metadata.source,
                    "title": chunk.metadata.title,
                    "doc_type": chunk.metadata.doc_type,
                    "language": chunk.metadata.language,
                    "ingested_at": chunk.metadata.ingested_at.isoformat(),
                },
            )
            points.append(point)

        if not points:
            return 0

        self.client.upsert(
            collection_name=self.collection_name,
            points=points,
        )

        logger.info("Upserted %d chunks into '%s'", len(points), self.collection_name)
        return len(points)

    async def search(
        self,
        query_embedding: list[float],
        top_k: int = 5,
        score_threshold: float = 0.5,
        source_filter: str | None = None,
    ) -> list[SearchResult]:
        query_filter = None
        if source_filter:
            query_filter = Filter(
                must=[
                    FieldCondition(
                        key="source",
                        match=MatchValue(value=source_filter),
                    )
                ]
            )

        results = await self.async_client.query_points(
            collection_name=self.collection_name,
            query=query_embedding,
            limit=top_k,
            score_threshold=score_threshold,
            query_filter=query_filter,
            with_payload=True,
        )

        search_results = []
        for point in results.points:
            payload = point.payload or {}

            from app.models.schemas import DocumentMetadata, DocumentChunk
            chunk = DocumentChunk(
                chunk_id=payload.get("chunk_id", str(point.id)),
                text=payload.get("text", ""),
                chunk_index=payload.get("chunk_index", 0),
                metadata=DocumentMetadata(
                    source=payload.get("source", ""),
                    title=payload.get("title", ""),
                    doc_type=payload.get("doc_type", "markdown"),
                    language=payload.get("language", "en"),
                ),
                embedding=None,
            )

            search_results.append(
                SearchResult(chunk=chunk, score=point.score)
            )

        logger.info(
            "Search returned %d results (threshold=%.2f)",
            len(search_results),
            score_threshold,
        )

        return search_results

    async def get_collection_info(self) -> dict:
        try:
            if not self.async_client:
                raise RuntimeError("Qdrant client not initialized")

            info = await self.async_client.get_collection(self.collection_name)
            return {
                "name": self.collection_name,
                "points_count": info.points_count,
                "status": str(info.status),
            }
        except Exception as e:
            return {"name": self.collection_name, "error": str(e)}


# Singleton
retrieval_service = RetrievalService()