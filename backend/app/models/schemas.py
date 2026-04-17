from datetime import datetime, timezone
from pydantic import BaseModel, Field

class DocumentMetadata(BaseModel):

    source: str = Field(
        description="Ruta o URL del documento original. "
        "Ej: 'docs/fastapi/routing.md' o 'https://docs.python.org/3/tutorial'"
    )
    title: str = Field(
        default="",
        description="Título del documento. Se extrae del primer # en Markdown "
        "o del metadata del PDF.",
    )
    doc_type: str = Field(
        default="markdown",
        description="Tipo de documento: 'markdown', 'pdf', 'text'. "
        "Determina qué parser usar en la ingesta.",
    )
    language: str = Field(
        default="en",
        description="Idioma del documento. Puede afectar el tokenizer "
        "y el modelo de embeddings.",
    )
    ingested_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp de cuándo se ingirió el documento.",
    )


class DocumentChunk(BaseModel):

    chunk_id: str = Field(
        description="ID único del chunk. Formato: '{doc_hash}_{chunk_index}'. "
        "Ej: 'a1b2c3d4_0', 'a1b2c3d4_1'",
    )
    text: str = Field(
        description="Contenido textual del chunk.",
    )
    chunk_index: int = Field(
        description="Posición del chunk dentro del documento original. "
        "0 = primer chunk, 1 = segundo, etc.",
    )
    metadata: DocumentMetadata = Field(
        description="Metadata del documento fuente al que pertenece este chunk.",
    )
    embedding: list[float] | None = Field(
        default=None,
        description="Vector de embedding del chunk. None si aún no se ha calculado. "
        "Dimensiones dependen del modelo (1536 para text-embedding-3-small).",
    )



class SearchQuery(BaseModel):

    query: str = Field(
        description="Texto de la pregunta del usuario.",
        min_length=1,
        max_length=2000,
    )
    top_k: int = Field(
        default=5,
        ge=1,
        le=20,
        description="Cuántos resultados retornar. "
        "Más = más contexto pero más tokens y más costo.",
    )
    score_threshold: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Score mínimo de similitud para incluir un resultado. "
        "0.0 = todo, 1.0 = solo matches perfectos. "
        "0.5 es un buen default — filtra ruido sin perder resultados útiles.",
    )


class SearchResult(BaseModel):

    chunk: DocumentChunk
    score: float = Field(
        description="Similitud coseno entre la query y este chunk. "
        "Rango: 0.0 a 1.0.",
    )


class SearchResponse(BaseModel):
    query: str
    results: list[SearchResult]
    total_results: int



class ChatMessage(BaseModel):

    role: str = Field(description="Rol: 'user', 'assistant', o 'system'.")
    content: str = Field(description="Contenido del mensaje.")
    timestamp: datetime = Field(default_factory=lambda:datetime.now(timezone.utc))


class ChatRequest(BaseModel):
    message: str = Field(
        description="Mensaje del usuario.",
        min_length=1,
        max_length=5000,
    )
    conversation_id: str | None = Field(
        default=None,
        description="ID de la conversación. None = nueva conversación.",
    )


class ChatResponse(BaseModel):
    message: str = Field(description="Respuesta generada por el agente.")
    conversation_id: str = Field(description="ID de la conversación.")
    sources: list[SearchResult] = Field(
        default_factory=list,
        description="Chunks del RAG que se usaron para generar la respuesta. "
        "Permite al frontend mostrar 'fuentes' al usuario.",
    )
    tools_used: list[str] = Field(
        default_factory=list,
        description="Herramientas MCP que el agente usó. "
        "Ej: ['github_search', 'code_executor']",
    )



class IngestRequest(BaseModel):
    source: str = Field(
        description="Ruta al archivo o URL del documento a ingestar.",
    )
    doc_type: str = Field(
        default="markdown",
        description="Tipo: 'markdown', 'pdf', 'text'.",
    )


class IngestResponse(BaseModel):
    source: str
    chunks_created: int = Field(
        description="Cuántos chunks se generaron del documento.",
    )
    status: str = Field(
        default="success",
        description="Estado de la ingesta: 'success' o 'error'.",
    )
    message: str = Field(
        default="",
        description="Mensaje adicional (ej: error details).",
    )