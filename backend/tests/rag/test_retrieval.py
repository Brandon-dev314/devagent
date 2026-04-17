"""
Tests para los schemas del RAG y validación de datos.

Estos tests verifican que los schemas de Pydantic validan
correctamente los datos de entrada y salida del pipeline.
No necesitan servicios externos.

¿Por qué testear schemas?
Porque son tu CONTRATO. Si alguien cambia un campo de Optional
a Required sin querer, estos tests lo atrapan antes de que
llegue a producción.
"""

import pytest
from pydantic import ValidationError

from app.models.schemas import (
    DocumentMetadata,
    DocumentChunk,
    SearchQuery,
    SearchResult,
    ChatRequest,
    IngestRequest,
)


class TestDocumentMetadata:
    """Tests para DocumentMetadata schema."""

    def test_defaults_are_applied(self):
        """Metadata con solo source debe tener defaults razonables."""
        meta = DocumentMetadata(source="test.md")
        assert meta.source == "test.md"
        assert meta.doc_type == "markdown"
        assert meta.language == "en"
        assert meta.title == ""

    def test_custom_values(self):
        """Debe aceptar valores custom."""
        meta = DocumentMetadata(
            source="docs/api.pdf",
            title="API Reference",
            doc_type="pdf",
            language="es",
        )
        assert meta.title == "API Reference"
        assert meta.doc_type == "pdf"
        assert meta.language == "es"


class TestDocumentChunk:
    """Tests para DocumentChunk schema."""

    def test_chunk_without_embedding(self):
        """Un chunk recién creado no tiene embedding."""
        chunk = DocumentChunk(
            chunk_id="abc123_0",
            text="Some text content",
            chunk_index=0,
            metadata=DocumentMetadata(source="test.md"),
        )
        assert chunk.embedding is None

    def test_chunk_with_embedding(self):
        """Un chunk puede tener un embedding asignado."""
        embedding = [0.1] * 1536
        chunk = DocumentChunk(
            chunk_id="abc123_0",
            text="Some text content",
            chunk_index=0,
            metadata=DocumentMetadata(source="test.md"),
            embedding=embedding,
        )
        assert chunk.embedding is not None
        assert len(chunk.embedding) == 1536


class TestSearchQuery:

    def test_valid_query(self):
        """Query válida con defaults."""
        q = SearchQuery(query="How do I use FastAPI?")
        assert q.query == "How do I use FastAPI?"
        assert q.top_k == 5
        assert q.score_threshold == 0.5

    def test_custom_top_k(self):
        """Debe aceptar top_k custom dentro del rango."""
        q = SearchQuery(query="test", top_k=10)
        assert q.top_k == 10

    def test_empty_query_rejected(self):
        """Query vacía debe ser rechazada por min_length=1."""
        with pytest.raises(ValidationError):
            SearchQuery(query="")

    def test_top_k_too_high_rejected(self):
        """top_k > 20 debe ser rechazado."""
        with pytest.raises(ValidationError):
            SearchQuery(query="test", top_k=50)

    def test_top_k_zero_rejected(self):
        """top_k = 0 no tiene sentido, debe ser rechazado."""
        with pytest.raises(ValidationError):
            SearchQuery(query="test", top_k=0)

    def test_score_threshold_range(self):
        """score_threshold debe estar entre 0 y 1."""
        # Válidos
        SearchQuery(query="test", score_threshold=0.0)
        SearchQuery(query="test", score_threshold=1.0)

        # Inválidos
        with pytest.raises(ValidationError):
            SearchQuery(query="test", score_threshold=-0.1)
        with pytest.raises(ValidationError):
            SearchQuery(query="test", score_threshold=1.5)


class TestChatRequest:
    """Tests para ChatRequest schema."""

    def test_valid_request(self):
        """Request básica válida."""
        req = ChatRequest(message="Hello!")
        assert req.message == "Hello!"
        assert req.conversation_id is None

    def test_with_conversation_id(self):
        """Request con conversation_id existente."""
        req = ChatRequest(message="Follow up", conversation_id="conv_123")
        assert req.conversation_id == "conv_123"

    def test_empty_message_rejected(self):
        """Mensaje vacío debe ser rechazado."""
        with pytest.raises(ValidationError):
            ChatRequest(message="")


class TestIngestRequest:
    """Tests para IngestRequest schema."""

    def test_valid_request(self):
        req = IngestRequest(source="docs/intro.md")
        assert req.source == "docs/intro.md"
        assert req.doc_type == "markdown"

    def test_custom_doc_type(self):
        req = IngestRequest(source="report.pdf", doc_type="pdf")
        assert req.doc_type == "pdf"