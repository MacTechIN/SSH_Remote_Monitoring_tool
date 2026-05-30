"use client";

import { Badge, Button } from "@/components/ui";

export default function DesignPreviewPage() {
  return (
    <div>
      <h1>Design Preview</h1>
      <p style={{ color: "var(--color-text-secondary)" }}>Figma 교체 전 토큰·primitive 확인</p>
      <div style={{ display: "flex", gap: "var(--spacing-md)", marginTop: "var(--spacing-md)" }}>
        <Button variant="primary">Primary</Button>
        <Button variant="secondary">Secondary</Button>
        <Button variant="ghost">Ghost</Button>
        <Button variant="danger">Danger</Button>
      </div>
      <div style={{ display: "flex", gap: "var(--spacing-sm)", marginTop: "var(--spacing-md)" }}>
        <Badge kind="system">system</Badge>
        <Badge kind="user">user</Badge>
        <Badge kind="unknown">unknown</Badge>
      </div>
      <div style={{ display: "flex", gap: 3, marginTop: "var(--spacing-lg)" }}>
        {[0, 1, 2, 3, 4].map((l) => (
          <div
            key={l}
            style={{
              width: 16,
              height: 16,
              borderRadius: "var(--radius-sm)",
              background: `var(--activity-${l})`,
            }}
          />
        ))}
      </div>
    </div>
  );
}
