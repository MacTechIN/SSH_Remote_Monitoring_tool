import type { ReactNode } from "react";
import { Button } from "@/components/ui";
import type { Host } from "@/lib/api";

export interface HostsViewProps {
  hosts: Host[];
  onTest: (id: string) => void;
  onCollect: (id: string) => void;
  form: ReactNode;
}

export function HostsView({ hosts, onTest, onCollect, form }: HostsViewProps) {
  return (
    <div data-figma-component="Hosts/List">
      <h1 style={{ fontSize: "var(--font-size-xl)" }}>호스트 관리</h1>
      {form}
      <ul style={{ listStyle: "none", padding: 0, marginTop: "var(--spacing-lg)" }}>
        {hosts.map((h) => (
          <li
            key={h.id}
            style={{
              padding: "var(--spacing-md)",
              border: "1px solid var(--color-border)",
              borderRadius: "var(--radius-md)",
              marginBottom: "var(--spacing-sm)",
            }}
          >
            <strong>{h.name}</strong> — {h.ssh_user}@{h.hostname}:{h.port}
            <div style={{ marginTop: "var(--spacing-sm)", display: "flex", gap: "var(--spacing-sm)" }}>
              <Button variant="secondary" size="sm" onClick={() => onTest(h.id)}>
                연결 테스트
              </Button>
              <Button variant="primary" size="sm" onClick={() => onCollect(h.id)}>
                지금 수집
              </Button>
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}
