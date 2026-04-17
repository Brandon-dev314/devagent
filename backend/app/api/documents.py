import logging
from fastapi import APIRouter, HTTPException

from app.models.schemas import (
    IngestRequest,
    IngestResponse,
    SearchQuery,
    SearchResponse,
)
from app.rag.ingestion import ingestion_pipeline
from app.rag.embeddings import embedding_service
from app.rag.retrieval import retrieval_service

logger = logging.getLogger("devagent.api.documents")

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("/ingest", response_model=IngestResponse)
async def ingest_document(request: IngestRequest):
    try:
        ingestion_pipeline.ensure_collection()

        result = ingestion_pipeline.ingest_file(request.source)

        if result.status == "error":
            raise HTTPException(status_code=400, detail=result.message)

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error("❌ Ingestion failed: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {str(e)}")


@router.post("/search", response_model=SearchResponse)
async def search_documents(query: SearchQuery):
    try:
        query_embedding = await embedding_service.aembed_query(query.query)

        results = await retrieval_service.search(
            query_embedding=query_embedding,
            top_k=query.top_k,
            score_threshold=query.score_threshold,
        )

        return SearchResponse(
            query=query.query,
            results=results,
            total_results=len(results),
        )

    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.error("❌ Search failed: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@router.get("/info")
async def collection_info():
    try:
        info = await retrieval_service.get_collection_info()
        return info
    except Exception as e:
        return {"error": str(e)}