"use client";

import { useEffect, useState } from "react";
import { LoginGate } from "@/components/auth/LoginGate";
import { DashboardContainer } from "@/components/features/Dashboard/DashboardContainer";
import { api, type Host } from "@/lib/api";

export default function HomePage() {
  const [hosts, setHosts] = useState<Host[]>([]);

  useEffect(() => {
    api.hosts.list().then(setHosts).catch(() => setHosts([]));
  }, []);

  return (
    <LoginGate>
      <DashboardContainer hosts={hosts} />
    </LoginGate>
  );
}
