import hashlib
import re

from app.config import settings
from app.models.schemas import DocumentChunk, DocumentMetadata

class RecursiveChunker:
    
    def __init__(self, chunk_size: int | None = None, chunk_overlap: int | None = None, separators: list[str] | None = None):
        
        self.chunk_size = chunk_size or settings.chunk_size
        self.chunk_overlap = chunk_overlap  or settings.chunk_overlap
        
        self.separators = separators or [
            "\n\n",
            "\n",
            ". ",
            "? ",
            "! ",
            "; ",
            ", ",
            " ",
            "",
        ]
    def chunk_text(self, text: str, metadata: DocumentMetadata) -> list[DocumentChunk]:
        text = self._clean_text(text)
        if not text.strip():
            return []
        doc_hash = hashlib.md5(text.encode()).hexdigest()[:8]
        raw_chunks = self._split_recursive(text, self.separators)
        chunks = []
        for i, chunk_text in enumerate(raw_chunks):
            chunk = DocumentChunk(
                chunk_id=f"{doc_hash}_{i}",
                text=chunk_text.strip(),
                chunk_index=i,
                metadata=metadata,
            )
            chunks.append(chunk)
        return chunks
    
    def _split_recursive(self, text: str, separators: list[str]) -> list[str]:
        if not text:
            return []
        if len(text) <= self.chunk_size:
            return [text]
        if not separators:
            return self._split_by_size(text)
        
        separator = separators[0]
        remaining_separators = separators[1:]
        
        if separator =="":
            return self._split_by_size(text)
        parts = text.split(separator)
        chunks = []
        current_chunk = ""
        for part in parts:
            
            candidate = (
                current_chunk + separator + part if current_chunk else part
            )
            if len(candidate) <= self.chunk_size:
                current_chunk = candidate
            else:
                if current_chunk:
                    chunks.append(current_chunk)
                
                if len(part) > self.chunk_size:
                    sub_chunks = self._split_recursive(part, remaining_separators)
                    chunks.extend(sub_chunks)
                    current_chunk = ""
                else:
                    current_chunk = part
        if current_chunk:
            chunks.append(current_chunk)
        if self.chunk_overlap >0:
            chunks = self._apply_overlap(chunks)
        return chunks
    
    def _apply_overlap(self, chunks: list[str]) -> list[str]:
    
        if len(chunks) <= 1:
            return chunks
 
        overlapped = [chunks[0]]
 
        for i in range(1, len(chunks)):
            prev = chunks[i - 1]
            current = chunks[i]
 
            overlap_text = prev[-self.chunk_overlap:]
 
            space_idx = overlap_text.find(" ")
            if space_idx != -1:
                overlap_text = overlap_text[space_idx + 1:]
 
            overlapped.append(overlap_text + " " + current)
 
        return overlapped
 
    def _split_by_size(self, text: str) -> list[str]:
        chunks = []
        for i in range(0, len(text), self.chunk_size - self.chunk_overlap):
            chunk = text[i:i + self.chunk_size]
            if chunk.strip():
                chunks.append(chunk)
        return chunks
 
    def _clean_text(self, text: str) -> str:

        text = text.replace("\r\n", "\n")
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()
 
 
chunker = RecursiveChunker()