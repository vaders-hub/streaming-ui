"use client";

import { StreamingCard } from "@/components/StreamingCard";
import { SSEMessage } from "@/hooks/useSSE";

export default function BasicPage() {
  return (
    <div className="container mx-auto px-4 py-8">
      <div className="mb-8 text-center">
        <h1 className="text-4xl font-bold tracking-tight">Basic Examples</h1>
        <p className="mt-2 text-lg text-muted-foreground">
          기본적인 SSE 스트리밍 시나리오 (Counter, Timestamp, Database)
        </p>
      </div>

      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        <StreamingCard
          title="Counter Stream"
          description="Real-time counter updates"
          endpoint="/stream/counter"
          renderMessage={(message: SSEMessage) => (
            <div className="flex items-center justify-between rounded-md bg-muted p-3">
              <span className="font-semibold">Count:</span>
              <span className="text-lg font-bold text-primary">
                {message.data.count}
              </span>
            </div>
          )}
        />

        <StreamingCard
          title="Timestamp Stream"
          description="Server time updates"
          endpoint="/stream/timestamp"
          renderMessage={(message: SSEMessage) => (
            <div className="rounded-md bg-muted p-3">
              <p className="text-xs text-muted-foreground">
                {message.data.message}
              </p>
              <p className="mt-1 font-mono text-xs">
                {new Date(message.data.current_time).toLocaleTimeString()}
              </p>
            </div>
          )}
        />

        <StreamingCard
          title="Database Stream"
          description="Oracle database updates"
          endpoint="/stream/database"
          method="POST"
          body={{}}
          renderMessage={(message: SSEMessage) => (
            <div className="rounded-md bg-muted p-3">
              <div className="flex items-center justify-between">
                <span className="text-xs text-muted-foreground">
                  DB Time:
                </span>
                <span className="font-mono text-xs">
                  {message.data.db_time || "N/A"}
                </span>
              </div>
              <div className="mt-1 flex items-center justify-between">
                <span className="text-xs text-muted-foreground">Count:</span>
                <span className="font-semibold">{message.data.count}</span>
              </div>
            </div>
          )}
        />

        <StreamingCard
          title="Oracle Telemetry Stream"
          description="DB time, USER_OBJECTS count, query latency"
          endpoint="/stream/oracle/telemetry"
          method="POST"
          body={{}}
          renderMessage={(message: SSEMessage) => (
            <div className="rounded-md bg-muted p-3 space-y-1">
              <div className="flex items-center justify-between">
                <span className="text-xs text-muted-foreground">DB Time:</span>
                <span className="font-mono text-xs">
                  {message.data.db_time || "N/A"}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-xs text-muted-foreground">
                  USER_OBJECTS:
                </span>
                <span className="font-semibold">{message.data.object_count}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-xs text-muted-foreground">Query:</span>
                <span className="font-mono text-xs">
                  {message.data.query_ms} ms
                </span>
              </div>
            </div>
          )}
        />

        <StreamingCard
          title="Oracle ORDERS Change Stream"
          description="Change events (new orders + status changes)"
          endpoint="/stream/oracle/orders/changes"
          method="POST"
          body={{ limit: 50, poll_interval: 2.0 }}
          renderMessage={(message: SSEMessage) => {
            // Filter: only show actual change events (not ready/heartbeat messages)
            if (message.data.type !== "oracle_orders_change") {
              return null;
            }

            const kind = message.data.kind;
            const order = message.data.order || {};
            return (
              <div className="rounded-md bg-muted p-3 space-y-1">
                <div className="flex items-center justify-between">
                  <span className="text-xs text-muted-foreground">Kind:</span>
                  <span className="text-xs font-semibold">{kind}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-xs text-muted-foreground">Order:</span>
                  <span className="font-mono text-xs">#{order.order_id}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-xs text-muted-foreground">Status:</span>
                  <span className="text-xs">
                    {kind === "status_changed"
                      ? `${order.old_status} → ${order.new_status}`
                      : order.status}
                  </span>
                </div>
              </div>
            );
          }}
        />
      </div>
    </div>
  );
}
