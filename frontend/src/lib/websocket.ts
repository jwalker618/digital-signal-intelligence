// A-3g: WebSocket client.
//
// Connects to /ws?token=<access_token> from the infrastructure side.
// Emits server-sent events (audit mutations, recalibration state,
// config changes, ...) to subscribed listeners.
//
// Reconnects with exponential backoff on close. Sends periodic pings
// to keep the connection live through idle proxies.

export interface WSEvent {
  type: string;
  resource_type?: string;
  resource_id?: string;
  tenant_id?: string;
  action_type?: string;
  [key: string]: unknown;
}

type Listener = (event: WSEvent) => void;

export class DSIWebSocket {
  private url: string;
  private token: string | null = null;
  private socket: WebSocket | null = null;
  private listeners = new Set<Listener>();
  private backoffMs = 1_000;
  private pingInterval: ReturnType<typeof setInterval> | null = null;
  private explicitlyClosed = false;

  constructor(baseUrl?: string) {
    const api = baseUrl ?? process.env.NEXT_PUBLIC_API_URL ?? "";
    // Convert http(s) -> ws(s); fall back to current origin if api is relative.
    if (/^https?:\/\//i.test(api)) {
      this.url = api.replace(/^http/i, "ws") + "/ws";
    } else if (typeof window !== "undefined") {
      const proto = window.location.protocol === "https:" ? "wss" : "ws";
      this.url = `${proto}://${window.location.host}/ws`;
    } else {
      this.url = "ws://localhost:8000/ws";
    }
  }

  connect(token: string): void {
    this.token = token;
    this.explicitlyClosed = false;
    this.openSocket();
  }

  private openSocket() {
    if (!this.token) return;
    if (typeof WebSocket === "undefined") return;
    try {
      const ws = new WebSocket(`${this.url}?token=${encodeURIComponent(this.token)}`);
      this.socket = ws;

      ws.onopen = () => {
        this.backoffMs = 1_000;
        this.pingInterval = setInterval(() => {
          if (ws.readyState === WebSocket.OPEN) ws.send("ping");
        }, 30_000);
      };

      ws.onmessage = (ev) => {
        if (ev.data === "pong") return;
        try {
          const parsed = JSON.parse(ev.data) as WSEvent;
          for (const listener of this.listeners) listener(parsed);
        } catch {
          // ignore non-JSON frames
        }
      };

      ws.onclose = () => {
        if (this.pingInterval) clearInterval(this.pingInterval);
        this.pingInterval = null;
        this.socket = null;
        if (this.explicitlyClosed) return;
        // Exponential backoff reconnect, capped at 30s.
        const delay = Math.min(this.backoffMs, 30_000);
        setTimeout(() => this.openSocket(), delay);
        this.backoffMs = Math.min(this.backoffMs * 2, 30_000);
      };

      ws.onerror = () => {
        try {
          ws.close();
        } catch {
          // ignore
        }
      };
    } catch {
      // Will retry on next tick via the backoff loop below
      setTimeout(() => this.openSocket(), Math.min(this.backoffMs, 30_000));
      this.backoffMs = Math.min(this.backoffMs * 2, 30_000);
    }
  }

  onEvent(listener: Listener): () => void {
    this.listeners.add(listener);
    return () => this.listeners.delete(listener);
  }

  disconnect(): void {
    this.explicitlyClosed = true;
    if (this.pingInterval) clearInterval(this.pingInterval);
    this.pingInterval = null;
    try {
      this.socket?.close();
    } catch {
      // ignore
    }
    this.socket = null;
    this.token = null;
  }
}

// Module-level singleton -- pages/components share a single connection.
let singleton: DSIWebSocket | null = null;

export function getDsiWebSocket(): DSIWebSocket {
  if (!singleton) singleton = new DSIWebSocket();
  return singleton;
}
