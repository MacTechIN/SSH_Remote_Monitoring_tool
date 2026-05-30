"use client";

import { useCallback, useEffect, useState } from "react";
import { Button } from "@/components/ui";
import { api, type Host } from "@/lib/api";
import { HostsView } from "./HostsView";

export function HostsContainer() {
  const [hosts, setHosts] = useState<Host[]>([]);
  const [name, setName] = useState("");
  const [hostname, setHostname] = useState("");
  const [sshUser, setSshUser] = useState("root");
  const [privateKey, setPrivateKey] = useState("");

  const refresh = useCallback(async () => {
    try {
      setHosts(await api.hosts.list());
    } catch {
      setHosts([]);
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  const onCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    await api.hosts.create({
      name,
      hostname,
      ssh_user: sshUser,
      private_key: privateKey,
      port: 22,
      poll_interval_sec: 60,
    });
    setName("");
    setHostname("");
    setPrivateKey("");
    refresh();
  };

  const form = (
    <form onSubmit={onCreate} style={{ display: "grid", gap: "var(--spacing-sm)", maxWidth: 480 }}>
      <input placeholder="이름" value={name} onChange={(e) => setName(e.target.value)} required />
      <input placeholder="hostname" value={hostname} onChange={(e) => setHostname(e.target.value)} required />
      <input placeholder="SSH user" value={sshUser} onChange={(e) => setSshUser(e.target.value)} required />
      <textarea
        placeholder="PEM private key"
        value={privateKey}
        onChange={(e) => setPrivateKey(e.target.value)}
        rows={4}
        required
      />
      <Button type="submit">호스트 추가</Button>
    </form>
  );

  return (
    <HostsView
      hosts={hosts}
      form={form}
      onTest={async (id) => {
        const r = await api.hosts.test(id);
        alert(r.ok ? "연결 성공" : "연결 실패");
      }}
      onCollect={async (id) => {
        await api.hosts.collect(id);
        alert("수집 완료");
      }}
    />
  );
}
