"use client";

import Link from "next/link";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { ArrowRight, Layers, MessageSquare } from "lucide-react";

export default function Home() {
  return (
    <div className="container mx-auto px-4 py-16">
      <div className="mb-12 text-center">
        <h1 className="text-5xl font-extrabold tracking-tight mb-4">
            SSE Streaming Dashboard
          </h1>
        <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
          Server-Sent Events를 활용한 실시간 데이터 스트리밍 예제 프로젝트입니다.
          기본적인 데이터 전송부터 LLM 채팅까지 확인해보세요.
          </p>
        </div>

      <div className="grid gap-8 md:grid-cols-2 max-w-4xl mx-auto">
        <Card className="flex flex-col">
          <CardHeader>
            <Layers className="h-10 w-10 text-primary mb-2" />
            <CardTitle className="text-2xl">Basic Examples</CardTitle>
            <CardDescription>
              Counter, Timestamp, Oracle Database와 연동된 기본적인 SSE 스트리밍을 확인합니다.
            </CardDescription>
          </CardHeader>
          <CardContent className="mt-auto pt-4">
            <Link href="/basic">
              <Button className="w-full">
                Go to Basic <ArrowRight className="ml-2 h-4 w-4" />
              </Button>
            </Link>
          </CardContent>
        </Card>

        <Card className="flex flex-col">
          <CardHeader>
            <MessageSquare className="h-10 w-10 text-primary mb-2" />
            <CardTitle className="text-2xl">Chat Example</CardTitle>
            <CardDescription>
              OpenAI와 연동된 LLM 응답을 Zustand Store를 활용하여 스트리밍 방식으로 출력합니다.
            </CardDescription>
          </CardHeader>
          <CardContent className="mt-auto pt-4">
            <Link href="/chat">
              <Button className="w-full">
                Go to Chat <ArrowRight className="ml-2 h-4 w-4" />
              </Button>
            </Link>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
