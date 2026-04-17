import logging
from pathlib import Path

from app.models.schemas import DocumentMetadata, DocumentChunk, IngestResponse
from app.rag.chunking import RecursiveChunker
from app.rag.embeddings import EmbeddingService
from app.rag.retrieval import RetrievalService

logger = logging.getLogger("devagent.ingestion")
EMBEDDING_BATCH_SIZE = 50


class IngestionPipeline:
    def __init__(
        self,
        chunker: RecursiveChunker | None = None,
        embedding_service: EmbeddingService | None = None,
        retrieval_service: RetrievalService | None = None,
    ):
        self.chunker = chunker or RecursiveChunker()
        self.embedding_service = embedding_service or EmbeddingService()
        self.retrieval_service = retrieval_service or RetrievalService()

    def ensure_collection(self) -> None:
        self.retrieval_service.ensure_collection()

    def ingest_file(self, file_path: str) -> IngestResponse:
        path = Path(file_path)

        logger.info("Reading file: %s", path)

        if not path.exists():
            return IngestResponse(
                source=str(path),
                chunks_created=0,
                status="error",
                message=f"File not found: {path}",
            )

        doc_type = self._detect_doc_type(path)
        text = self._read_file(path, doc_type)

        if not text.strip():
            return IngestResponse(
                source=str(path),
                chunks_created=0,
                status="error",
                message="File is empty or could not be read",
            )

        title = self._extract_title(text, doc_type)

        metadata = DocumentMetadata(
            source=str(path),
            title=title,
            doc_type=doc_type,
        )

        logger.info("Chunking document...")
        chunks = self.chunker.chunk_text(text, metadata)
        logger.info("   → %d chunks created", len(chunks))

        if not chunks:
            return IngestResponse(
                source=str(path),
                chunks_created=0,
                status="error",
                message="No chunks generated (document too short?)",
            )

        logger.info("Generating embeddings...")
        chunks = self._embed_chunks(chunks)

        logger.info("Storing in Qdrant...")
        stored = self.retrieval_service.upsert_chunks(chunks)

        logger.info(
            "Ingestion complete: %s → %d chunks stored",
            path.name,
            stored,
        )

        return IngestResponse(
            source=str(path),
            chunks_created=stored,
            status="success",
        )

    def ingest_directory(self, dir_path: str, extensions: list[str] | None = None) -> list[IngestResponse]:
        extensions = extensions or [".md", ".txt"]
        path = Path(dir_path)

        if not path.is_dir():
            logger.error("❌ Directory not found: %s", path)
            return []

        files = []
        for ext in extensions:
            files.extend(path.rglob(f"*{ext}"))

        logger.info("📁 Found %d files in %s", len(files), path)

        results = []
        for file in sorted(files):
            result = self.ingest_file(str(file))
            results.append(result)

        total_chunks = sum(r.chunks_created for r in results)
        successes = sum(1 for r in results if r.status == "success")
        logger.info(
            "📊 Ingestion summary: %d/%d files successful, %d total chunks",
            successes,
            len(results),
            total_chunks,
        )

        return results

    def _embed_chunks(self, chunks: list[DocumentChunk]) -> list[DocumentChunk]:
        texts = [chunk.text for chunk in chunks]

        all_embeddings = []
        for i in range(0, len(texts), EMBEDDING_BATCH_SIZE):
            batch = texts[i:i + EMBEDDING_BATCH_SIZE]
            batch_embeddings = self.embedding_service.embed_texts(batch)
            all_embeddings.extend(batch_embeddings)

            logger.info(
                "   → Embedded batch %d/%d (%d texts)",
                i // EMBEDDING_BATCH_SIZE + 1,
                (len(texts) - 1) // EMBEDDING_BATCH_SIZE + 1,
                len(batch),
            )

        for chunk, embedding in zip(chunks, all_embeddings):
            chunk.embedding = embedding

        return chunks

    def _read_file(self, path: Path, doc_type: str) -> str:
        if doc_type == "pdf":
            logger.warning("⚠️ PDF reading not yet implemented, skipping: %s", path)
            return ""

        try:
            return path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            try:
                return path.read_text(encoding="latin-1")
            except Exception as e:
                logger.error("❌ Could not read %s: %s", path, e)
                return ""

    def _detect_doc_type(self, path: Path) -> str:
        suffix = path.suffix.lower()
        type_map = {
            ".md": "markdown",
            ".markdown": "markdown",
            ".txt": "text",
            ".pdf": "pdf",
            ".html": "html",
            ".htm": "html",
            ".rst": "text",
        }
        return type_map.get(suffix, "text")

    def _extract_title(self, text: str, doc_type: str) -> str:
   
        lines = text.strip().split("\n")

        if doc_type == "markdown":
            for line in lines:
                line = line.strip()
                if line.startswith("# "):
                    return line[2:].strip()

        for line in lines:
            line = line.strip()
            if line:
                return line[:100]  

        return "Untitled"


# Singleton
ingestion_pipeline = IngestionPipeline()