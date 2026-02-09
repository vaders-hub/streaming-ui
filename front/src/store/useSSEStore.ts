import { create } from "zustand";
import { SSEMessage } from "@/hooks/useSSE";

interface StreamState {
  messages: Record<string, SSEMessage[]>;
  isConnected: Record<string, boolean>;
  errors: Record<string, string | null>;
  
  // Actions
  addMessage: (key: string, message: SSEMessage) => void;
  setConnected: (key: string, connected: boolean) => void;
  setError: (key: string, error: string | null) => void;
  clearMessages: (key: string) => void;
}

export const useSSEStore = create<StreamState>((set) => ({
  messages: {},
  isConnected: {},
  errors: {},

  addMessage: (key, message) =>
    set((state) => ({
      messages: {
        ...state.messages,
        [key]: [...(state.messages[key] || []), message],
      },
    })),

  setConnected: (key, connected) =>
    set((state) => ({
      isConnected: { ...state.isConnected, [key]: connected },
    })),

  setError: (key, error) =>
    set((state) => ({
      errors: { ...state.errors, [key]: error },
    })),

  clearMessages: (key) =>
    set((state) => ({
      messages: { ...state.messages, [key]: [] },
    })),
}));
