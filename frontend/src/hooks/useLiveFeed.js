import { useEffect, useRef, useState } from "react";

const MAX_BUFFERED_EVENTS = 40;

/**
 * Connects to the /ws/live endpoint, keeps a rolling buffer of the most
 * recent events, and reconnects with backoff if the connection drops --
 * a real dashboard has to survive backend restarts and flaky networks.
 */
export function useLiveFeed() {
  const [events, setEvents] = useState([]);
  const [status, setStatus] = useState("connecting");
  const retryDelay = useRef(1000);

  useEffect(() => {
    let socket;
    let reconnectTimer;
    let cancelled = false;

    const connect = () => {
      const protocol = window.location.protocol === "https:" ? "wss" : "ws";
      socket = new WebSocket(`${protocol}://${window.location.host}/ws/live`);

      socket.onopen = () => {
        setStatus("connected");
        retryDelay.current = 1000;
      };

      socket.onmessage = (raw) => {
        try {
          const msg = JSON.parse(raw.data);
          if (msg.type === "event") {
            setEvents((prev) => [msg.data, ...prev].slice(0, MAX_BUFFERED_EVENTS));
          }
        } catch {
          // ignore malformed frames
        }
      };

      socket.onclose = () => {
        if (cancelled) return;
        setStatus("reconnecting");
        reconnectTimer = setTimeout(connect, retryDelay.current);
        retryDelay.current = Math.min(retryDelay.current * 1.5, 10000);
      };

      socket.onerror = () => {
        socket.close();
      };
    };

    connect();

    return () => {
      cancelled = true;
      clearTimeout(reconnectTimer);
      socket?.close();
    };
  }, []);

  return { events, status };
}
