/** Firebase Hosting: same-origin /api rewrite → Cloud Functions */
const API_URL =
  process.env.NEXT_PUBLIC_DEPLOY_TARGET === "firebase"
    ? ""
    : (process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000");

export const isFirebaseDeploy = process.env.NEXT_PUBLIC_DEPLOY_TARGET === "firebase";

let authToken: string | null = null;

export function setAuthToken(token: string | null) {
  authToken = token;
  if (typeof window !== "undefined") {
    if (token) sessionStorage.setItem("token", token);
    else sessionStorage.removeItem("token");
  }
}

export function getAuthToken(): string | null {
  if (authToken) return authToken;
  if (typeof window !== "undefined") {
    authToken = sessionStorage.getItem("token");
  }
  return authToken;
}

export async function login(username: string, password: string): Promise<string> {
  const res = await fetch(`${API_URL}/api/v1/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password }),
  });
  if (!res.ok) throw new Error("Login failed");
  const data = (await res.json()) as { access_token: string };
  setAuthToken(data.access_token);
  return data.access_token;
}

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const token = getAuthToken();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
  };
  if (token) headers.Authorization = `Bearer ${token}`;

  const res = await fetch(`${API_URL}${path}`, { ...init, headers });
  if (res.status === 401 && typeof window !== "undefined") {
    setAuthToken(null);
  }
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || res.statusText);
  }
  if (res.status === 204) return undefined as T;
  return res.json() as Promise<T>;
}

export interface Host {
  id: string;
  name: string;
  hostname: string;
  port: number;
  ssh_user: string;
  poll_interval_sec: number;
  enabled: boolean;
}

export interface LiveSnapshot {
  snapshot_id: string;
  host_id: string;
  collected_at: string;
  processes: Array<{
    pid: number;
    user: string;
    comm: string;
    cmd: string;
    classification: string;
    cpu_percent: number | null;
  }>;
  sessions: Array<{ user: string; tty: string | null }>;
}

export const api = {
  hosts: {
    list: () => apiFetch<Host[]>("/api/v1/hosts"),
    live: (id: string) => apiFetch<LiveSnapshot>(`/api/v1/hosts/${id}/live`),
    create: (body: Record<string, unknown>) =>
      apiFetch<Host>("/api/v1/hosts", { method: "POST", body: JSON.stringify(body) }),
    test: (id: string) => apiFetch<{ ok: boolean }>(`/api/v1/hosts/${id}/test-connection`, { method: "POST" }),
    collect: (id: string) =>
      apiFetch<{ ok: boolean }>(`/api/v1/hosts/${id}/collect`, { method: "POST" }),
  },
  activity: {
    calendar: (from: string, to: string, hostId?: string) => {
      const q = new URLSearchParams({ from, to });
      if (hostId) q.set("host_id", hostId);
      return apiFetch<{ cells: Array<{ date: string; level: number; count: number }> }>(
        `/api/v1/activity/calendar?${q}`,
      );
    },
    daySummary: (date: string, hostId?: string) => {
      const q = new URLSearchParams({ date });
      if (hostId) q.set("host_id", hostId);
      return apiFetch<{ lines: Array<{ user: string; summary: string }> }>(
        `/api/v1/activity/day-summary?${q}`,
      );
    },
  },
  search: {
    processes: (params: Record<string, string>) => {
      const q = new URLSearchParams(params);
      return apiFetch<{ items: Array<Record<string, unknown>>; total: number }>(
        `/api/v1/search/processes?${q}`,
      );
    },
  },
};

export function wsLiveUrl(hostId: string): string | null {
  if (isFirebaseDeploy) return null;
  const base = (API_URL || "http://localhost:8000").replace(/^http/, "ws");
  return `${base}/ws/v1/live?host_id=${hostId}`;
}
