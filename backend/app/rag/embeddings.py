import logging
from openai import OpenAI, AsyncOpenAI

from app.config import settings

logger = logging.getLogger("devagent.embeddings")


EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIMENSIONS = 1536


class EmbeddingService:


    def __init__(self, api_key: str | None = None):

        key = api_key or settings.openai_api_key
        if not key:
            logger.warning(
                " OPENAI_API_KEY no configurada. "
                "Los embeddings no funcionarán hasta que la configures."
            )
        self.client = OpenAI(api_key=key) if key else None
        self.async_client = AsyncOpenAI(api_key=key) if key else None

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        
        if not self.client:
            raise RuntimeError(
                "OpenAI client no inicializado. ¿Configuraste OPENAI_API_KEY?"
            )

        if not texts:
            return []

        clean_texts = [t if t.strip() else " " for t in texts]

        logger.info("Generating embeddings for %d texts...", len(clean_texts))

        response = self.client.embeddings.create(
            model=EMBEDDING_MODEL,
            input=clean_texts,
        )

        embeddings = [item.embedding for item in sorted(response.data, key=lambda x: x.index)]

        logger.info("Generated %d embeddings (%d dimensions each)",
                     len(embeddings), len(embeddings[0]))

        return embeddings

    async def aembed_texts(self, texts: list[str]) -> list[list[float]]:

        if not self.async_client:
            raise RuntimeError(
                "OpenAI async client no inicializado. ¿Configuraste OPENAI_API_KEY?"
            )

        if not texts:
            return []

        clean_texts = [t if t.strip() else " " for t in texts]

        response = await self.async_client.embeddings.create(
            model=EMBEDDING_MODEL,
            input=clean_texts,
        )

        embeddings = [item.embedding for item in sorted(response.data, key=lambda x: x.index)]
        return embeddings

    async def aembed_query(self, query: str) -> list[float]:

        embeddings = await self.aembed_texts([query])
        return embeddings[0]


embedding_service = EmbeddingService()