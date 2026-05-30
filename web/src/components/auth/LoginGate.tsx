"use client";

import { useState } from "react";
import { Button } from "@/components/ui";
import { useAuth } from "@/hooks/useAuth";

export function LoginGate({ children }: { children: React.ReactNode }) {
  const { ready, authenticated, signIn } = useAuth();
  const [username, setUsername] = useState("admin");
  const [password, setPassword] = useState("admin");
  const [error, setError] = useState("");

  if (!ready) return <p>…</p>;
  if (authenticated) return <>{children}</>;

  return (
    <div style={{ maxWidth: 360, margin: "var(--spacing-xl) auto" }}>
      <h1>로그인</h1>
      <form
        onSubmit={async (e) => {
          e.preventDefault();
          try {
            await signIn(username, password);
          } catch {
            setError("로그인 실패");
          }
        }}
      >
        <input value={username} onChange={(e) => setUsername(e.target.value)} placeholder="username" style={{ width: "100%", marginBottom: 8 }} />
        <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="password" style={{ width: "100%", marginBottom: 8 }} />
        <Button type="submit">로그인</Button>
      </form>
      {error && <p style={{ color: "var(--color-danger)" }}>{error}</p>}
    </div>
  );
}
