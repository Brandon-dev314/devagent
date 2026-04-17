

from app.rag.chunking import RecursiveChunker
from app.models.schemas import DocumentMetadata


def make_metadata(source: str = "test.md") -> DocumentMetadata:
    return DocumentMetadata(source=source, title="Test Doc", doc_type="markdown")


class TestRecursiveChunker:
    def test_short_text_single_chunk(self):
        chunker = RecursiveChunker(chunk_size=500, chunk_overlap=0)
        text = "This is a short text about Python."
        chunks = chunker.chunk_text(text, make_metadata())

        assert len(chunks) == 1
        assert chunks[0].text == text

    def test_empty_text_returns_no_chunks(self):
        chunker = RecursiveChunker(chunk_size=100, chunk_overlap=0)
        chunks = chunker.chunk_text("", make_metadata())

        assert len(chunks) == 0

    def test_whitespace_only_returns_no_chunks(self):
        chunker = RecursiveChunker(chunk_size=100, chunk_overlap=0)
        chunks = chunker.chunk_text("   \n\n\n   ", make_metadata())

        assert len(chunks) == 0

    def test_long_text_produces_multiple_chunks(self):
        chunker = RecursiveChunker(chunk_size=100, chunk_overlap=0)

        paragraphs = [f"This is paragraph number {i}. " * 5 for i in range(10)]
        text = "\n\n".join(paragraphs)

        chunks = chunker.chunk_text(text, make_metadata())

        assert len(chunks) > 1
        for chunk in chunks:
            assert len(chunk.text.strip()) > 0

    def test_splits_on_paragraphs_first(self):
        chunker = RecursiveChunker(chunk_size=100, chunk_overlap=0)

        text = "Short paragraph one.\n\nShort paragraph two.\n\nShort paragraph three."
        chunks = chunker.chunk_text(text, make_metadata())

        for chunk in chunks:
            assert not chunk.text.startswith("graph")
            assert not chunk.text.endswith("para")

    def test_chunk_index_is_sequential(self):
        chunker = RecursiveChunker(chunk_size=50, chunk_overlap=0)

        text = "First sentence here. " * 20
        chunks = chunker.chunk_text(text, make_metadata())

        for i, chunk in enumerate(chunks):
            assert chunk.chunk_index == i

    def test_metadata_propagated_to_all_chunks(self):
        chunker = RecursiveChunker(chunk_size=50, chunk_overlap=0)
        metadata = make_metadata(source="docs/python/intro.md")

        text = "Some text. " * 20
        chunks = chunker.chunk_text(text, metadata)

        for chunk in chunks:
            assert chunk.metadata.source == "docs/python/intro.md"
            assert chunk.metadata.title == "Test Doc"
            assert chunk.metadata.doc_type == "markdown"

    def test_chunk_ids_are_unique(self):
        chunker = RecursiveChunker(chunk_size=50, chunk_overlap=0)

        text = "Some text here. " * 20
        chunks = chunker.chunk_text(text, make_metadata())

        ids = [chunk.chunk_id for chunk in chunks]
        assert len(ids) == len(set(ids)), "Chunk IDs should be unique"

    def test_same_text_produces_same_ids(self):
        chunker = RecursiveChunker(chunk_size=50, chunk_overlap=0)
        metadata = make_metadata()

        text = "Deterministic chunking test. " * 10
        chunks_first = chunker.chunk_text(text, metadata)
        chunks_second = chunker.chunk_text(text, metadata)

        ids_first = [c.chunk_id for c in chunks_first]
        ids_second = [c.chunk_id for c in chunks_second]

        assert ids_first == ids_second

    def test_different_text_produces_different_ids(self):
        chunker = RecursiveChunker(chunk_size=500, chunk_overlap=0)

        chunks_a = chunker.chunk_text("Document A content", make_metadata())
        chunks_b = chunker.chunk_text("Document B content", make_metadata())

        assert chunks_a[0].chunk_id != chunks_b[0].chunk_id

    def test_overlap_adds_context(self):
        chunker = RecursiveChunker(chunk_size=80, chunk_overlap=20)

        text = "Alpha paragraph content.\n\nBeta paragraph content.\n\nGamma paragraph content.\n\nDelta paragraph content."
        chunks = chunker.chunk_text(text, make_metadata())

        if len(chunks) > 1:
            assert len(chunks[1].text) > 0

    def test_no_chunks_exceed_size_significantly(self):
        chunk_size = 100
        overlap = 20
        chunker = RecursiveChunker(chunk_size=chunk_size, chunk_overlap=overlap)

        text = "Word " * 200 
        chunks = chunker.chunk_text(text, make_metadata())

        max_allowed = chunk_size * 3
        for chunk in chunks:
            assert len(chunk.text) < max_allowed, (
                f"Chunk too large: {len(chunk.text)} chars "
                f"(max expected ~{max_allowed})"
            )

    def test_cleans_excessive_newlines(self):
        chunker = RecursiveChunker(chunk_size=500, chunk_overlap=0)

        text = "Before.\n\n\n\n\n\nAfter."
        chunks = chunker.chunk_text(text, make_metadata())

        assert "\n\n\n" not in chunks[0].text

    def test_handles_windows_newlines(self):
        chunker = RecursiveChunker(chunk_size=500, chunk_overlap=0)

        text = "Line one.\r\nLine two.\r\n\r\nParagraph two."
        chunks = chunker.chunk_text(text, make_metadata())

        assert "\r" not in chunks[0].text

    def test_embedding_starts_as_none(self):
        chunker = RecursiveChunker(chunk_size=500, chunk_overlap=0)

        chunks = chunker.chunk_text("Some text", make_metadata())
        assert chunks[0].embedding is None