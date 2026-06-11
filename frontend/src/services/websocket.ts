/// <reference types="vite/client" />

/**
 * WebSocket service that manages the connection lifecycle with the research backend.
 * Connects, sends the research question, dispatches incoming events to handlers,
 * and reconnects automatically on unexpected disconnection.
 */

export type EventType =
  | "thinking"
  | "tool_call"
  | "result"
  | "report"
  | "error"
  | "done";

export interface AgentEvent {
  type: EventType;
  message: string;
  data?: unknown;
}

export interface ResearchCallbacks {
  onEvent: (event: AgentEvent) => void;
  onClose: () => void;
  onError: (err: Event) => void;
}

const WS_BASE_URL = import.meta.env.VITE_WS_URL ?? "ws://localhost:8000";
const MAX_RECONNECT_ATTEMPTS = 3;
const RECONNECT_DELAY_MS = 2000;

export class ResearchWebSocket {
  private ws: WebSocket | null = null;
  private question: string = "";
  private callbacks: ResearchCallbacks;
  private reconnectAttempts = 0;
  private closed = false;

  constructor(callbacks: ResearchCallbacks) {
    this.callbacks = callbacks;
  }

  /** Open the WebSocket and start the research pipeline for the given question. */
  start(question: string): void {
    this.question = question;
    this.closed = false;
    this.reconnectAttempts = 0;
    this._connect();
  }

  /** Gracefully close the WebSocket connection. */
  stop(): void {
    this.closed = true;
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }

  private _connect(): void {
    const url = `${WS_BASE_URL}/ws/research`;
    this.ws = new WebSocket(url);

    this.ws.onopen = () => {
      this.reconnectAttempts = 0;
      // Send the research question as the first message after connecting
      this.ws?.send(JSON.stringify({ question: this.question }));
    };

    this.ws.onmessage = (event: MessageEvent) => {
      try {
        const parsed: AgentEvent = JSON.parse(event.data as string);
        if (parsed.type === "done" || parsed.type === "error") {
          this.closed = true;
        }
        this.callbacks.onEvent(parsed);
      } catch {
        // Malformed message from server — surface as an error event
        this.callbacks.onEvent({
          type: "error",
          message: `Failed to parse server message: ${event.data}`,
        });
      }
    };

    this.ws.onerror = (err: Event) => {
      this.callbacks.onError(err);
    };

    this.ws.onclose = () => {
      if (this.closed) {
        // Intentional close
        this.callbacks.onClose();
        return;
      }

      // Unexpected close — attempt reconnection
      if (this.reconnectAttempts < MAX_RECONNECT_ATTEMPTS) {
        this.reconnectAttempts++;
        setTimeout(() => {
          if (!this.closed) {
            this._connect();
          }
        }, RECONNECT_DELAY_MS * this.reconnectAttempts);
      } else {
        this.callbacks.onEvent({
          type: "error",
          message: `Connection lost after ${MAX_RECONNECT_ATTEMPTS} reconnection attempts.`,
        });
        this.callbacks.onClose();
      }
    };
  }
}
