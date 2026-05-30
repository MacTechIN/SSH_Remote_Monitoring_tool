import { Badge } from "@/components/ui";
import type { LiveSnapshot } from "@/lib/api";

export interface DashboardViewProps {
  hostName: string;
  snapshot: LiveSnapshot | null;
  loading: boolean;
  lastUpdated: string | null;
  wsConnected: boolean;
}

export function DashboardView({ hostName, snapshot, loading, lastUpdated, wsConnected }: DashboardViewProps) {
  return (
    <div data-figma-component="Dashboard/Default">
      <header style={{ marginBottom: "var(--spacing-lg)" }}>
        <h1 style={{ margin: 0, fontSize: "var(--font-size-xl)" }}>대시보드 — {hostName}</h1>
        <p style={{ color: "var(--color-text-secondary)", fontSize: "var(--font-size-sm)" }}>
          WS {wsConnected ? "연결됨" : "대기"} · 마지막 갱신 {lastUpdated ?? "—"}
        </p>
      </header>

      {loading && <p>로딩 중…</p>}

      {!loading && !snapshot && <p>스냅샷 없음. 호스트에서 수집을 실행하세요.</p>}

      {snapshot && (
        <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "var(--font-size-sm)" }}>
          <thead>
            <tr style={{ borderBottom: "1px solid var(--color-border)", textAlign: "left" }}>
              <th style={{ padding: "var(--spacing-sm)" }}>사용자</th>
              <th>프로세스</th>
              <th>분류</th>
              <th>CPU%</th>
            </tr>
          </thead>
          <tbody>
            {snapshot.processes.slice(0, 100).map((p) => (
              <tr key={`${p.pid}-${p.comm}`} style={{ borderBottom: "1px solid var(--color-border)" }}>
                <td style={{ padding: "var(--spacing-sm)" }}>{p.user}</td>
                <td title={p.cmd}>
                  {p.comm}
                </td>
                <td>
                  <Badge kind={p.classification as "system" | "user" | "unknown"}>{p.classification}</Badge>
                </td>
                <td>{p.cpu_percent ?? "—"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
