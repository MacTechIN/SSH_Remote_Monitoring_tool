import type { ReactNode } from "react";

export interface AppShellProps {
  /** Figma: sidebar / header 슬롯 — 레이아웃만 교체 */
  sidebar?: ReactNode;
  header?: ReactNode;
  children: ReactNode;
}

/**
 * Presentational shell — Figma `Layout / App Shell` 프레임과 매핑.
 * navigation 링크·로고 등은 Figma 교체 시 이 컴포넌트 내부만 수정.
 */
export function AppShell({ sidebar, header, children }: AppShellProps) {
  return (
    <div className="app-shell" data-figma-component="Layout/AppShell">
      {sidebar ? <aside className="app-shell__sidebar">{sidebar}</aside> : null}
      <div className="app-shell__main">
        {header ? <header className="app-shell__header">{header}</header> : null}
        <main className="app-shell__content">{children}</main>
      </div>
    </div>
  );
}
