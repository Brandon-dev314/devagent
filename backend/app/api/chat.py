import logging
from fastapi import APIRouter, HTTPException

from app.models.schemas import ChatRequest, ChatResponse
from app.agent.orchestrator import orchestrator
from app.agent.memory import memory_store

logger = logging.getLogger("devagent.api.chat")

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        response = await orchestrator.handle_message(request)
        return response

    except Exception as e:
        logger.error("❌ Chat failed: %s", e, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred processing your message: {str(e)}",
        )


@router.get("/conversations")
async def list_conversations():
    conversations = []
    for conv_id, memory in memory_store._conversations.items():
        conversations.append({
            "conversation_id": conv_id,
            "message_count": memory.message_count,
            "created_at": memory.created_at.isoformat(),
            "last_activity": memory.last_activity.isoformat(),
        })

    return {
        "active_conversations": len(conversations),
        "conversations": conversations,
    }


@router.delete("/conversations/{conversation_id}")
async def delete_conversation(conversation_id: str):
    deleted = memory_store.delete(conversation_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return {"status": "deleted", "conversation_id": conversation_id}