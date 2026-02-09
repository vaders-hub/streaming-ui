import logging
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Query, Request
from sse_starlette.sse import EventSourceResponse

from app.schemas.api import ChatRequest, ChunkMode
from app.services.chat_streaming import stream_openai_chat

router = APIRouter(prefix="/chat", tags=["Chat"])
# Uvicorn 기본 로깅 설정(handlers/format)을 그대로 타도록 uvicorn.error 하위 로거를 사용합니다.
logger = logging.getLogger("uvicorn.error").getChild("chat")


@router.get("/stream")
async def chat_stream_get(
    request: Request,
    q: str = Query(..., min_length=1, max_length=4000, description="User prompt"),
    mode: ChunkMode = Query("token", description="Chunking mode"),
    chunk_size: int = Query(80, ge=1, le=2000, description="Chunk size for chars/paragraph"),
) -> EventSourceResponse:
    """
    Stream chat completion tokens via SSE (GET).

    Args:
        request: HTTP request object
        q: User prompt
        mode: Chunking mode (token, chars, or paragraph)
        chunk_size: Chunk size used for chars/paragraph flushing

    Returns:
        EventSourceResponse with streaming chat completion

    Raises:
        HTTPException: If prompt is missing
    """
    if not q:
        raise HTTPException(status_code=400, detail="Missing query param: q")

    req_id = uuid4().hex[:8]
    client_ip = request.client.host if request and request.client else None

    logger.info(f"GET /chat/stream req_id={req_id} mode={mode}")

    return EventSourceResponse(
        stream_openai_chat(
            q,
            mode=mode,
            chunk_size=chunk_size,
            request_id=req_id,
            client_ip=client_ip,
        )
    )


@router.post("/stream")
async def chat_stream_post(
    request: ChatRequest, http_request: Request
) -> EventSourceResponse:
    """
    Stream chat completion tokens via SSE (POST).

    Supports longer prompts and secure data transmission.

    Args:
        request: Chat request with prompt and settings
        http_request: HTTP request object

    Returns:
        EventSourceResponse with streaming chat completion

    Raises:
        HTTPException: If prompt is missing
    """
    if not request.prompt:
        raise HTTPException(status_code=400, detail="Missing prompt")

    req_id = uuid4().hex[:8]
    client_ip = http_request.client.host if http_request and http_request.client else None

    logger.info(f"POST /chat/stream req_id={req_id} mode={request.mode}")

    return EventSourceResponse(
        stream_openai_chat(
            request.prompt,
            mode=request.mode,
            chunk_size=request.chunk_size,
            request_id=req_id,
            client_ip=client_ip,
        )
    )
