"use client";

import { useEffect, useRef } from "react";
import { wsLiveUrl } from "@/lib/api";

export function useLiveWebSocket(hostId: string | null, onMessage: () => void) {
  const cbRef = useRef(onMessage);
  cbRef.current = onMessage;

  useEffect(() => {
    if (!hostId) return;
    const url = wsLiveUrl(hostId);
    const ws = new WebSocket(url);
    ws.onmessage = () => cbRef.current();
    return () => ws.close();
  }, [hostId]);
}
