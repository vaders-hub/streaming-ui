"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useSSEStore } from "@/store/useSSEStore";
import { SSEClient, SSEClientOptions, SSEMessage } from "@/lib/sse-client";

// Re-export types for backward compatibility
export type { SSEMessage };

export interface UseSSEOptions extends Omit<SSEClientOptions, "onOpen" | "onMessage" | "onError" | "onClose"> {
  enabled?: boolean;
  storeKey?: string;
  storeMessages?: boolean;
  maxMessages?: number;
  onOpen?: () => void;
  onMessage?: (message: SSEMessage) => void;
  onError?: (error: Error) => void;
  onClose?: () => void;
}

export function useSSE({
  url,
  method = "GET",
  body,
  headers,
  enabled = true,
  storeKey,
  storeMessages = true,
  maxMessages = 500,
  autoReconnect = false,
  reconnectDelay = 3000,
  maxReconnectAttempts = 5,
  onOpen,
  onMessage,
  onError,
  onClose,
}: UseSSEOptions) {
  // ─── Local State ─────────────────────────────────────────
  const [localMessages, setLocalMessages] = useState<SSEMessage[]>([]);
  const [localIsConnected, setLocalIsConnected] = useState(false);
  const [localError, setLocalError] = useState<string | null>(null);

  // ─── Store Integration ───────────────────────────────────
  const {
    addMessage,
    setConnected,
    setError: setStoreError,
    clearMessages: clearStoreMessages,
  } = useSSEStore();

  const storeMessagesArr = useSSEStore((state) =>
    storeKey ? state.messages[storeKey] : undefined
  );
  const storeIsConnected = useSSEStore((state) =>
    storeKey ? state.isConnected[storeKey] : undefined
  );
  const storeError = useSSEStore((state) =>
    storeKey ? state.errors[storeKey] : undefined
  );

  // ─── Refs ────────────────────────────────────────────────
  const clientRef = useRef<SSEClient | null>(null);

  // ─── Helpers ─────────────────────────────────────────────
  const updateConnected = useCallback(
    (connected: boolean) => {
      if (storeKey) setConnected(storeKey, connected);
      setLocalIsConnected(connected);
    },
    [storeKey, setConnected]
  );

  const updateError = useCallback(
    (errMsg: string | null) => {
      if (storeKey) setStoreError(storeKey, errMsg);
      setLocalError(errMsg);
    },
    [storeKey, setStoreError]
  );

  const pushMessage = useCallback(
    (message: SSEMessage) => {
      if (!storeMessages) return;

      if (storeKey) {
        addMessage(storeKey, message);
      }
      setLocalMessages((prev) => {
        const updated = [...prev, message];
        return updated.length > maxMessages
          ? updated.slice(-maxMessages)
          : updated;
      });
    },
    [storeKey, storeMessages, maxMessages, addMessage]
  );

  // ─── Effect: Lifecycle ───────────────────────────────────
  useEffect(() => {
    if (!enabled || !url) {
      updateConnected(false);
      return;
    }

    const client = new SSEClient({
      url,
      method,
      body,
      headers,
      autoReconnect,
      reconnectDelay,
      maxReconnectAttempts,
      onOpen: () => {
        updateConnected(true);
        updateError(null);
        onOpen?.();
      },
      onMessage: (msg) => {
        pushMessage(msg);
        onMessage?.(msg);
      },
      onError: (err) => {
        updateConnected(false);
        updateError(err.message);
        onError?.(err);
      },
      onClose: () => {
        updateConnected(false);
        onClose?.();
      },
    });

    clientRef.current = client;
    client.connect();

    return () => {
      client.disconnect();
      clientRef.current = null;
      updateConnected(false);
    };
  }, [
    url,
    method,
    // Note: body object reference might change, but we assume stable usage or useMemo in parent
    // If strict deep compare is needed, implement useDeepCompareEffect or similar
    JSON.stringify(body), 
    JSON.stringify(headers),
    enabled,
    autoReconnect,
    reconnectDelay,
    maxReconnectAttempts,
    updateConnected,
    updateError,
    pushMessage,
    onOpen,
    onMessage,
    onError,
    onClose,
  ]);

  // ─── Actions ─────────────────────────────────────────────
  const disconnect = useCallback(() => {
    clientRef.current?.disconnect();
    updateConnected(false);
  }, [updateConnected]);

  const clearMessages = useCallback(() => {
    if (storeKey) {
      clearStoreMessages(storeKey);
    }
    setLocalMessages([]);
  }, [storeKey, clearStoreMessages]);

  const reconnect = useCallback(() => {
    disconnect();
    // Small delay to allow cleanup? Or just call connect immediately?
    // SSEClient.connect handles re-initialization.
    if (enabled && url) {
        // Trigger effect re-run or manually connect?
        // Ideally we let effect handle it, but if we want manual reconnect:
        clientRef.current?.connect();
    }
  }, [disconnect, enabled, url]);

  // ─── Return ──────────────────────────────────────────────
  return {
    messages: storeKey ? storeMessagesArr || [] : localMessages,
    isConnected: storeKey ? storeIsConnected || false : localIsConnected,
    error: storeKey ? storeError || null : localError,
    disconnect,
    clearMessages,
    reconnect,
  };
}
