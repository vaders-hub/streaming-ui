"use client";

import { useCallback, useMemo, useState } from "react";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { useSSE } from "@/hooks/useSSE";
import { useSSEStore } from "@/store/useSSEStore";
import { PlayCircle, StopCircle, Trash2, RefreshCw } from "lucide-react";

export function ChatCard() {
  const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
  const storeKey = "llm-chat";

  const [prompt, setPrompt] = useState(
    "안녕하세요! SSE로 스트리밍되는 LLM 채팅을 보여주세요."
  );
  const [mode, setMode] = useState<"token" | "chars" | "paragraph">("token");
  const [chunkSize, setChunkSize] = useState(80);
  const [usePost, setUsePost] = useState(true);
  
  // SSE 연결용 상태
  const [sseEnabled, setSseEnabled] = useState(false);
  const [currentRequest, setCurrentRequest] = useState<{
    url: string;
    body?: Record<string, unknown>;
  } | null>(null);

  const clearStoreMessages = useSSEStore((state) => state.clearMessages);

  const { messages, isConnected, error, disconnect, clearMessages, reconnect } =
    useSSE({
      url: currentRequest?.url || "",
      method: usePost ? "POST" : "GET",
      body: currentRequest?.body,
      enabled: sseEnabled && !!currentRequest?.url,
      storeKey,
      storeMessages: true,
      maxMessages: 100,
      autoReconnect: false,
      onMessage: (msg) => {
        const t = msg.data?.type;
        if (t === "chat_error" || t === "chat_done") {
          setSseEnabled(false);
        }
      },
      onError: (err) => {
        console.error("SSE Error:", err);
        setSseEnabled(false);
      },
    });

  // assistant 내용을 store의 messages로부터 계산
  const assistant = useMemo(() => {
    return messages
      .filter((m) => m.data?.type === "chat_delta")
      .map((m) => m.data.delta || "")
      .join("");
  }, [messages]);

  // chat_error 타입의 메시지 확인
  const chatError = useMemo(() => {
    const lastErrorMsg = [...messages]
      .reverse()
      .find((m) => m.data?.type === "chat_error");
    return lastErrorMsg?.data?.error || null;
  }, [messages]);

  const handleStart = useCallback(() => {
    // 먼저 메시지 클리어
    clearMessages();
    
    // 요청 정보 설정
    if (usePost) {
      setCurrentRequest({
        url: `${apiUrl}/chat/stream`,
        body: {
          prompt,
          mode,
          chunk_size: chunkSize,
        },
      });
    } else {
      const qs = new URLSearchParams({
        q: prompt,
        mode,
        chunk_size: String(chunkSize),
      });
      setCurrentRequest({
        url: `${apiUrl}/chat/stream?${qs.toString()}`,
        body: undefined,
      });
    }
    
    // SSE 활성화
    setSseEnabled(true);
  }, [apiUrl, prompt, mode, chunkSize, usePost, clearMessages]);

  const handleStop = useCallback(() => {
    setSseEnabled(false);
    disconnect();
  }, [disconnect]);

  const handleClear = useCallback(() => {
    clearMessages();
    setCurrentRequest(null);
  }, [clearMessages]);

  const handleRetry = useCallback(() => {
    if (currentRequest) {
      clearMessages();
      setSseEnabled(true);
    }
  }, [currentRequest, clearMessages]);

  return (
    <Card className="w-full">
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          LLM Chat Stream (Enhanced)
          <div className="flex items-center gap-2">
            <div
              className={`h-2 w-2 rounded-full ${
                isConnected ? "bg-green-500" : "bg-gray-300"
              }`}
            />
            <span className="text-xs font-normal text-muted-foreground">
              {isConnected ? "Connected" : "Disconnected"}
            </span>
          </div>
        </CardTitle>
        <CardDescription>
          Fetch 기반 SSE (POST/GET 지원, Zustand Store 연동)
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-3">
        {(chatError || error) && (
          <div className="rounded-md bg-destructive/10 p-3 text-sm text-destructive">
            {chatError || error}
          </div>
        )}

        <div className="space-y-2">
          <label className="text-xs text-muted-foreground">Prompt</label>
          <textarea
            className="min-h-20 w-full resize-y rounded-md border bg-background p-3 text-sm outline-none focus:ring-2 focus:ring-ring"
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            disabled={isConnected}
            placeholder="질문을 입력하세요..."
          />
        </div>

        <div className="grid gap-2 md:grid-cols-3">
          <div className="space-y-2">
            <label className="text-xs text-muted-foreground">
              HTTP Method
            </label>
            <select
              className="w-full rounded-md border bg-background p-2 text-sm outline-none focus:ring-2 focus:ring-ring"
              value={usePost ? "POST" : "GET"}
              onChange={(e) => setUsePost(e.target.value === "POST")}
              disabled={isConnected}
            >
              <option value="POST">POST (권장)</option>
              <option value="GET">GET (기존 방식)</option>
            </select>
          </div>
          <div className="space-y-2">
            <label className="text-xs text-muted-foreground">Chunk mode</label>
            <select
              className="w-full rounded-md border bg-background p-2 text-sm outline-none focus:ring-2 focus:ring-ring"
              value={mode}
              onChange={(e) => setMode(e.target.value as any)}
              disabled={isConnected}
            >
              <option value="token">token (기본)</option>
              <option value="chars">chars (글자수 기준)</option>
              <option value="paragraph">paragraph (단락/문장 기준)</option>
            </select>
          </div>
          <div className="space-y-2">
            <label className="text-xs text-muted-foreground">Chunk size</label>
            <input
              className="w-full rounded-md border bg-background p-2 text-sm outline-none focus:ring-2 focus:ring-ring"
              type="number"
              min={1}
              max={2000}
              value={chunkSize}
              onChange={(e) => setChunkSize(Number(e.target.value || 80))}
              disabled={isConnected || mode === "token"}
            />
          </div>
        </div>

        <div className="space-y-2">
          <label className="text-xs text-muted-foreground">Assistant</label>
          <div className="min-h-28 whitespace-pre-wrap rounded-md border bg-muted/30 p-3 text-sm">
            {assistant ? (
              assistant
            ) : (
              <span className="text-muted-foreground">
                Start를 누르면 토큰이 실시간으로 출력됩니다.
              </span>
            )}
          </div>
        </div>
      </CardContent>
      <CardFooter className="flex gap-2">
        {!isConnected ? (
          <Button onClick={handleStart} size="sm" disabled={!prompt.trim()}>
            <PlayCircle className="mr-2 h-4 w-4" />
            Start
          </Button>
        ) : (
          <Button onClick={handleStop} variant="destructive" size="sm">
            <StopCircle className="mr-2 h-4 w-4" />
            Stop
          </Button>
        )}

        <Button
          onClick={handleClear}
          variant="outline"
          size="sm"
          disabled={!assistant}
        >
          <Trash2 className="mr-2 h-4 w-4" />
          Clear
        </Button>

        <Button
          onClick={handleRetry}
          variant="ghost"
          size="sm"
          disabled={isConnected || !currentRequest}
        >
          <RefreshCw className="mr-2 h-4 w-4" />
          Retry
        </Button>
      </CardFooter>
    </Card>
  );
}
