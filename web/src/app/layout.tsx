import type { Metadata } from "next";
import { AppShell } from "@/components/layouts/AppShell";
import "./globals.css";

export const metadata: Metadata = {
  title: "SSH Remote Monitor",
  description: "Remote process monitoring dashboard",
};

function NavSidebar() {
  return (
    <nav className="app-nav">
      <strong style={{ display: "block", marginBottom: "var(--spacing-md)" }}>SSH Monitor</strong>
      <a href="/">대시보드</a>
      <br />
      <a href="/activity">활동</a>
      <br />
      <a href="/hosts">호스트</a>
      <br />
      <a href="/search">검색</a>
      <br />
      <a href="/design-preview">디자인</a>
    </nav>
  );
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ko" data-theme="dark">
      <body>
        <AppShell sidebar={<NavSidebar />}>{children}</AppShell>
      </body>
    </html>
  );
}
