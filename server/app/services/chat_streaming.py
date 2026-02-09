import asyncio
import json
import logging
import time
from datetime import datetime
from collections.abc import AsyncGenerator, AsyncIterator

from openai.types.chat import ChatCompletionChunk

from app.core.config import settings
from app.schemas.api import ChunkMode

logger = logging.getLogger(__name__)


class ChatStreamLogger:
    """Context manager for chat stream logging and metrics."""

    def __init__(
        self, req_id: str, client_ip: str | None, mode: str, chunk_size: int, prompt_preview: str
    ):
        self.req_id = req_id
        self.client_ip = client_ip
        self.mode = mode
        self.chunk_size = chunk_size
        self.prompt_preview = prompt_preview
        self.start_time = 0.0
        self.first_token_time: float | None = None
        self.emitted_chunks = 0
        self.error: Exception | None = None

    def __enter__(self):
        self.start_time = time.time()
        logger.info(
            "chat_stream [START] req_id=%s client=%s mode=%s chunk_size=%s prompt=[%s]",
            self.req_id,
            self.client_ip or "-",
            self.mode,
            self.chunk_size,
            self.prompt_preview,
        )
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = time.time() - self.start_time
        if exc_type:
            if exc_type is asyncio.CancelledError:
                logger.info(
                    "chat_stream [CANCELLED] req_id=%s duration=%.2fs emitted_chunks=%s",
                    self.req_id,
                    duration,
                    self.emitted_chunks,
                )
            else:
                logger.exception(
                    "chat_stream [ERROR] req_id=%s client=%s error=%s",
                    self.req_id,
                    self.client_ip or "-",
                    exc_val,
                )
        else:
            logger.info(
                "chat_stream [DONE] req_id=%s duration=%.2fs emitted_chunks=%s",
                self.req_id,
                duration,
                self.emitted_chunks,
            )

    def log_first_token(self):
        if self.first_token_time is None:
            self.first_token_time = time.time()
            latency = (self.first_token_time - self.start_time) * 1000
            logger.info(
                "chat_stream [FIRST_TOKEN] req_id=%s latency=%.2fms",
                self.req_id,
                latency,
            )

    def increment_emitted(self):
        self.emitted_chunks += 1


def _is_paragraph_boundary(text: str) -> bool:
    """Check if text contains paragraph or sentence boundary."""
    if "\n\n" in text:
        return True
    stripped = text.rstrip()
    if not stripped:
        return False
    punct = (".", "!", "?", "…", "。", "！", "？")
    return stripped.endswith(punct) or stripped.endswith("\n")


def _create_event(event_type: str, **kwargs) -> dict[str, str]:
    """Create a standardized SSE event dictionary."""
    data = {"type": event_type, "timestamp": datetime.now().isoformat(), **kwargs}
    return {"event": "message", "data": json.dumps(data)}


async def _generate_chunks(
    stream: AsyncIterator[ChatCompletionChunk],
    mode: ChunkMode,
    chunk_size: int,
    monitor: ChatStreamLogger,
) -> AsyncIterator[str]:
    """Process OpenAI stream and yield cleaned chunks based on mode."""
    buffer = ""
    flush_threshold = max(chunk_size, settings.chat_paragraph_flush_threshold)

    async for chunk in stream:
        monitor.log_first_token()
        
        delta = chunk.choices[0].delta.content if chunk.choices else None
        if not delta:
            continue

        if mode == "token":
            yield delta
        else:
            buffer += delta
            should_flush = False
            
            if mode == "chars" and len(buffer) >= chunk_size:
                should_flush = True
            elif mode == "paragraph":
                if _is_paragraph_boundary(buffer) or len(buffer) >= flush_threshold:
                    should_flush = True
            
            if should_flush:
                yield buffer
                buffer = ""
        
        # Keep loop cooperative
        await asyncio.sleep(0)

    if buffer:
        yield buffer


async def stream_openai_chat(
    prompt: str,
    mode: ChunkMode = "token",
    chunk_size: int = 80,
    request_id: str | None = None,
    client_ip: str | None = None,
) -> AsyncGenerator[dict[str, str], None]:
    """Generate streaming chat response from OpenAI."""
    req_id = request_id or "unknown"

    if not settings.openai_api_key:
        yield _create_event("chat_error", error="OPENAI_API_KEY is not set")
        return

    try:
        from openai import AsyncOpenAI
    except ImportError as e:
        yield _create_event("chat_error", error=f"OpenAI SDK not installed: {e}")
        return

    # Prepare prompt preview
    preview_len = settings.chat_prompt_preview_length
    prompt_preview = (
        (prompt[:preview_len] + "...") if len(prompt) > preview_len else prompt
    ).replace("\n", " ")

    monitor = ChatStreamLogger(req_id, client_ip, mode, chunk_size, prompt_preview)

    with monitor:
        try:
            client = AsyncOpenAI(api_key=settings.openai_api_key)
            stream = await client.chat.completions.create(
                model=settings.openai_model,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": prompt},
                ],
                stream=True,
            )

            async for content in _generate_chunks(stream, mode, chunk_size, monitor):
                yield _create_event("chat_delta", delta=content)
                monitor.increment_emitted()

            yield _create_event("chat_done")

        except Exception as e:
            if not isinstance(e, asyncio.CancelledError):
                yield _create_event("chat_error", error=str(e))
            raise
