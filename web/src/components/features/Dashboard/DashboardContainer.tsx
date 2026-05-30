"use client";

import { useCallback, useEffect, useState } from "react";
import { api, type Host, type LiveSnapshot } from "@/lib/api";
import { useLiveWebSocket } from "@/hooks/useLiveWebSocket";
import { DashboardView } from "./DashboardView";

export function DashboardContainer({ hosts }: { hosts: Host[] }) {
  const [hostId, setHostId] = useState<string | null>(hosts[0]?.id ?? null);
  const [snapshot, setSnapshot] = useState<LiveSnapshot | null>(null);
  const [loading, setLoading] = useState(false);
  const [wsConnected, setWsConnected] = useState(false);

  const load = useCallback(async () => {
    if (!hostId) return;
    setLoading(true);
    try {
      const data = await api.hosts.live(hostId);
      setSnapshot(data);
    } catch {
      setSnapshot(null);
    } finally {
      setLoading(false);
    }
  }, [hostId]);

  useEffect(() => {
    load();
  }, [load]);

  useLiveWebSocket(hostId, load);

  useEffect(() => {
    if (!hostId) return;
    setWsConnected(true);
  }, [hostId]);

  const hostName = hosts.find((h) => h.id === hostId)?.name ?? "—";

  return (
    <div>
      {hosts.length > 1 && (
        <select
          value={hostId ?? ""}
          onChange={(e) => setHostId(e.target.value)}
          style={{ marginBottom: "var(--spacing-md)" }}
        >
          {hosts.map((h) => (
            <option key={h.id} value={h.id}>
              {h.name}
            </option>
          ))}
        </select>
      )}
      <DashboardView
        hostName={hostName}
        snapshot={snapshot}
        loading={loading}
        lastUpdated={snapshot?.collected_at ?? null}
        wsConnected={wsConnected}
      />
    </div>
  );
}
