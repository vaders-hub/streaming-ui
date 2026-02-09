"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { useSSE, SSEMessage } from "@/hooks/useSSE";
import { PlayCircle, StopCircle, Trash2 } from "lucide-react";

interface StreamingCardProps {
  title: string;
  description: string;
  endpoint: string;
  method?: "GET" | "POST";
  body?: Record<string, unknown>;
  renderMessage: (message: SSEMessage) => React.ReactNode;
}

export function StreamingCard({
  title,
  description,
  endpoint,
  method = "GET",
  body,
  renderMessage,
}: StreamingCardProps) {
  const [enabled, setEnabled] = useState(false);
  const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

  // endpoint를 기반으로 고유한 storeKey 생성
  const storeKey = `stream-${endpoint.replace(/\//g, "-")}`;

  const { messages, isConnected, error, clearMessages, disconnect } = useSSE({
    url: `${apiUrl}${endpoint}`,
    method,
    body,
    enabled,
    storeKey, // 전역 Store 연동
  });

  const handleStart = () => {
    setEnabled(true);
  };

  const handleStop = () => {
    setEnabled(false);
    disconnect();
  };

  const handleClear = () => {
    clearMessages();
  };

  return (
    <Card className="w-full">
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          {title}
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
        <CardDescription>{description}</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-2">
          {error && (
            <div className="rounded-md bg-destructive/10 p-3 text-sm text-destructive">
              {error}
            </div>
          )}
          <div className="max-h-64 overflow-y-auto space-y-2 rounded-md border p-4">
            {messages.length === 0 ? (
              <p className="text-sm text-muted-foreground">
                No messages yet. Click Start to begin streaming.
              </p>
            ) : (
              [...messages].reverse().map((message, index) => (
                <div key={index} className="text-sm">
                  {renderMessage(message)}
                </div>
              ))
            )}
          </div>
        </div>
      </CardContent>
      <CardFooter className="flex gap-2">
        {!isConnected ? (
          <Button onClick={handleStart} size="sm">
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
          disabled={messages.length === 0}
        >
          <Trash2 className="mr-2 h-4 w-4" />
          Clear
        </Button>
      </CardFooter>
    </Card>
  );
}
