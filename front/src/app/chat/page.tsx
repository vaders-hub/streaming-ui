"use client";

import { ChatCard } from "@/components/ChatCard";

export default function ChatPage() {
  return (
    <div className="container mx-auto px-4 py-8">
      <div className="mb-8 text-center">
        <h1 className="text-4xl font-bold tracking-tight">Chat Example</h1>
        <p className="mt-2 text-lg text-muted-foreground">
          Zustand Store와 연동된 LLM 스트리밍 채팅 예제
        </p>
      </div>

      <div className="max-w-2xl mx-auto">
        <ChatCard />
      </div>
    </div>
  );
}
