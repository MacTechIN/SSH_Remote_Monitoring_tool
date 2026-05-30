"use client";

import { useState } from "react";
import { Button } from "@/components/ui";
import { api } from "@/lib/api";

export function SearchContainer() {
  const [user, setUser] = useState("");
  const [q, setQ] = useState("");
  const [items, setItems] = useState<Array<Record<string, unknown>>>([]);

  const onSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    const params: Record<string, string> = {};
    if (user) params.user = user;
    if (q) params.q = q;
    const res = await api.search.processes(params);
    setItems(res.items);
  };

  return (
    <div data-figma-component="Search/Results">
      <h1 style={{ fontSize: "var(--font-size-xl)" }}>프로세스 검색</h1>
      <form onSubmit={onSearch} style={{ display: "flex", gap: "var(--spacing-sm)", marginBottom: "var(--spacing-md)" }}>
        <input placeholder="사용자" value={user} onChange={(e) => setUser(e.target.value)} />
        <input placeholder="명령어 포함" value={q} onChange={(e) => setQ(e.target.value)} />
        <Button type="submit">검색</Button>
      </form>
      <p style={{ color: "var(--color-text-secondary)" }}>{items.length}건</p>
      <ul style={{ fontSize: "var(--font-size-sm)" }}>
        {items.map((item, i) => (
          <li key={i} style={{ marginBottom: "var(--spacing-xs)" }}>
            {String(item.user)} — {String(item.comm)} — {String(item.cmd)?.slice(0, 80)}
          </li>
        ))}
      </ul>
    </div>
  );
}
