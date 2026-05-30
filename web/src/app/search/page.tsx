"use client";

import { LoginGate } from "@/components/auth/LoginGate";
import { SearchContainer } from "@/components/features/Search/SearchContainer";

export default function SearchPage() {
  return (
    <LoginGate>
      <SearchContainer />
    </LoginGate>
  );
}
