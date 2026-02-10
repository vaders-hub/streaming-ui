export interface SSEMessage {
  event: string;
  type: string;
  data: any;
  timestamp?: string;
}

export interface SSEClientOptions {
  url: string;
  method?: "GET" | "POST";
  body?: Record<string, unknown> | string;
  headers?: Record<string, string>;
  autoReconnect?: boolean;
  reconnectDelay?: number;
  maxReconnectAttempts?: number;
  onOpen?: () => void;
  onMessage?: (message: SSEMessage) => void;
  onError?: (error: Error) => void;
  onClose?: () => void;
}

interface SSEEventBuffer {
  event: string;
  data: string[];
  id?: string;
}

export class SSEClient {
  private abortController: AbortController | null = null;
  private reconnectTimeout: ReturnType<typeof setTimeout> | null = null;
  private reconnectAttempts = 0;
  private options: SSEClientOptions;

  constructor(options: SSEClientOptions) {
    this.options = { ...options };
  }

  public updateOptions(newOptions: Partial<SSEClientOptions>) {
    this.options = { ...this.options, ...newOptions };
  }

  public connect() {
    this.disconnect(false); // Clean up previous connection but don't reset attempts if reconnecting
    
    this.abortController = new AbortController();
    const signal = this.abortController.signal;

    const {
      url,
      method = "GET",
      body,
      headers,
      autoReconnect = false,
      reconnectDelay = 3000,
      maxReconnectAttempts = 5,
    } = this.options;

    const performConnect = async () => {
      try {
        const requestHeaders: Record<string, string> = {
          Accept: "text/event-stream",
          "Cache-Control": "no-cache",
          ...headers,
        };

        const requestInit: RequestInit = {
          method,
          headers: requestHeaders,
          signal,
        };

        if (method === "POST" && body) {
          requestHeaders["Content-Type"] = "application/json";
          requestInit.body =
            typeof body === "string" ? body : JSON.stringify(body);
        }

        const response = await fetch(url, requestInit);

        if (!response.ok) {
          throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        if (!response.body) {
          throw new Error("No response body");
        }

        // Connection successful
        this.reconnectAttempts = 0;
        this.options.onOpen?.();

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        const buffer: SSEEventBuffer = { event: "message", data: [] };
        let partial = "";

        while (true) {
          const { done, value } = await reader.read();

          if (done) {
            this.options.onClose?.();
            break;
          }

          partial += decoder.decode(value, { stream: true });
          const lines = partial.split("\n");
          partial = lines.pop() || "";

          for (const line of lines) {
            this.parseLine(line, buffer);
          }
        }
      } catch (err) {
        if (signal.aborted) return;

        const error = err instanceof Error ? err : new Error(String(err));
        this.options.onError?.(error);

        if (autoReconnect) {
          if (maxReconnectAttempts === 0 || this.reconnectAttempts < maxReconnectAttempts) {
            this.reconnectAttempts++;
            this.reconnectTimeout = setTimeout(() => {
              this.connect();
            }, reconnectDelay);
          }
        }
      }
    };

    performConnect();
  }

  public disconnect(resetAttempts = true) {
    if (this.abortController) {
      this.abortController.abort();
      this.abortController = null;
    }
    if (this.reconnectTimeout) {
      clearTimeout(this.reconnectTimeout);
      this.reconnectTimeout = null;
    }
    if (resetAttempts) {
      this.reconnectAttempts = 0;
    }
  }

  private parseLine(line: string, buffer: SSEEventBuffer) {
    const normalized = line.replace(/\r$/, "");
    
    if (normalized === "") {
      if (buffer.data.length > 0) {
        this.dispatchMessage(buffer);
      }
      return;
    }

    if (normalized.startsWith(":")) return;

    const colonIndex = normalized.indexOf(":");
    if (colonIndex === -1) return;

    const field = normalized.slice(0, colonIndex);
    let value = normalized.slice(colonIndex + 1);
    if (value.startsWith(" ")) value = value.slice(1);

    switch (field) {
      case "event":
        buffer.event = value;
        break;
      case "data":
        buffer.data.push(value);
        break;
      case "id":
        buffer.id = value;
        break;
    }
  }

  private dispatchMessage(buffer: SSEEventBuffer) {
    const rawData = buffer.data.join("\n");
    let parsedData: any = rawData;

    try {
      parsedData = JSON.parse(rawData);
    } catch {
      // Keep as string
    }

    const message: SSEMessage = {
      event: buffer.event || "message",
      type: typeof parsedData === "object" ? parsedData?.type || "message" : "message",
      data: parsedData,
      timestamp: typeof parsedData === "object" ? parsedData?.timestamp : undefined,
    };

    if (!message.timestamp) {
      message.timestamp = new Date().toISOString();
    }

    this.options.onMessage?.(message);

    // Reset buffer
    buffer.event = "message";
    buffer.data = [];
    buffer.id = undefined;
  }
}
