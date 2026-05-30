"use client";

import { LoginGate } from "@/components/auth/LoginGate";
import { HostsContainer } from "@/components/features/Hosts/HostsContainer";

export default function HostsPage() {
  return (
    <LoginGate>
      <HostsContainer />
    </LoginGate>
  );
}
