"use client";

import { useCallback, useEffect, useState } from "react";
import { getAuthToken, login } from "@/lib/api";

export function useAuth() {
  const [ready, setReady] = useState(false);
  const [authenticated, setAuthenticated] = useState(false);

  useEffect(() => {
    setAuthenticated(!!getAuthToken());
    setReady(true);
  }, []);

  const signIn = useCallback(async (username: string, password: string) => {
    await login(username, password);
    setAuthenticated(true);
  }, []);

  return { ready, authenticated, signIn };
}
