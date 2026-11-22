"use client";
import { useCallback, useEffect, useState } from "react";

export const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
const KEY = "cp_token";

// Tokens live in localStorage for this MVP. For production prefer an httpOnly cookie set by the API.
export const token = {
  get: (): string | null => {
    try { return typeof window === "undefined" ? null : window.localStorage.getItem(KEY); } catch { return null; }
  },
  set: (t: string) => { try { window.localStorage.setItem(KEY, t); } catch { /* storage unavailable */ } },
  clear: () => {
    try { window.localStorage.removeItem(KEY); } catch { /* storage unavailable */ }
    saved.clearAll(); // results saved for this tab belong to the user who is signing out
  },
};

/**
 * Results kept for this browser tab (sessionStorage), so a page still shows them after you
 * visit another page and come back. Cleared on sign-out; it can be empty, so pages never rely on it.
 */
const SAVED = "cp_saved:";
export const saved = {
  get<T>(key: string): T | null {
    try { const v = window.sessionStorage.getItem(SAVED + key); return v ? (JSON.parse(v) as T) : null; } catch { return null; }
  },
  set(key: string, value: unknown) {
    try { window.sessionStorage.setItem(SAVED + key, JSON.stringify(value)); } catch { /* storage full or unavailable */ }
  },
  drop(...keys: string[]) {
    try { keys.forEach((k) => window.sessionStorage.removeItem(SAVED + k)); } catch { /* storage unavailable */ }
  },
  clearAll() {
    try { Object.keys(window.sessionStorage).filter((k) => k.startsWith(SAVED)).forEach((k) => window.sessionStorage.removeItem(k)); }
    catch { /* storage unavailable */ }
  },
};

export class ApiError extends Error {
  constructor(public status: number, public code: string, message: string) {
    super(message);
  }
}

/** GET /meta: roles grouped into IT fields, for the two-step field -> role pickers. */
export type RoleRef = { key: string; label: string };
export type Meta = { roles: (RoleRef & { field: string })[]; fields: (RoleRef & { roles: RoleRef[] })[]; levels: string[]; statuses: string[] };

type Params = Record<string, string | number | boolean | undefined>;
type Opts = { method?: string; body?: unknown; form?: FormData; params?: Params };

// eslint-disable-next-line @typescript-eslint/no-explicit-any
export async function api<T = any>(path: string, opts: Opts = {}): Promise<T> {
  const url = new URL(`${API_URL}/api/v1${path}`);
  Object.entries(opts.params ?? {}).forEach(([k, v]) => {
    if (v !== undefined && v !== "") url.searchParams.set(k, String(v));
  });
  const headers: Record<string, string> = {};
  const t = token.get();
  if (t) headers.Authorization = `Bearer ${t}`;
  let body: BodyInit | undefined;
  if (opts.form) body = opts.form;
  else if (opts.body !== undefined) {
    headers["Content-Type"] = "application/json";
    body = JSON.stringify(opts.body);
  }
  let res: Response;
  try {
    res = await fetch(url, { method: opts.method ?? (body ? "POST" : "GET"), headers, body });
  } catch {
    throw new ApiError(0, "NETWORK", "Cannot reach the server. Check that the backend is running.");
  }
  if (res.status === 204) return undefined as T;
  const data = await res.json().catch(() => null);
  if (!res.ok) {
    const err = data?.error;
    if (res.status === 401 && !path.startsWith("/auth/") && typeof window !== "undefined") {
      token.clear();
      window.location.href = "/login";
    }
    throw new ApiError(res.status, err?.code ?? "ERROR", err?.message ?? "Something went wrong. Please try again.");
  }
  return data as T;
}

/** Fetches a file the API serves (such as the user's CV) with the sign-in token, as a Blob. */
export async function apiBlob(path: string): Promise<Blob> {
  const headers: Record<string, string> = {};
  const t = token.get();
  if (t) headers.Authorization = `Bearer ${t}`;
  let res: Response;
  try {
    res = await fetch(`${API_URL}/api/v1${path}`, { headers });
  } catch {
    throw new ApiError(0, "NETWORK", "Cannot reach the server. Check that the backend is running.");
  }
  if (!res.ok) {
    const data = await res.json().catch(() => null);
    throw new ApiError(res.status, data?.error?.code ?? "ERROR", data?.error?.message ?? "Could not load the file.");
  }
  return res.blob();
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
/**
 * Like useApi, but the result is kept for this browser tab under `key` (see `saved`), so returning to the
 * page shows it at once instead of running the agent again. `refresh()` runs it again on request.
 */
const inflight = new Map<string, Promise<unknown>>(); // one request per kept result, even if the page mounts twice

export function useSavedApi<T = any>(path: string, key: string) {
  const [result, setResult] = useState<{ data: T; at: string } | null>(null);
  const [error, setError] = useState<ApiError | null>(null);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async (force: boolean) => {
    const last = force ? null : saved.get<{ data: T; at: string }>(key);
    if (last) { setResult(last); setError(null); setLoading(false); return; }
    setLoading(true); setError(null);
    if (force) setResult(null);
    try {
      let req = inflight.get(key) as Promise<T> | undefined;
      if (!req) { req = api<T>(path); inflight.set(key, req); req.finally(() => inflight.delete(key)).catch(() => {}); }
      const fresh = { data: await req, at: new Date().toISOString() };
      setResult(fresh); saved.set(key, fresh);
    } catch (e) {
      setError(e instanceof ApiError ? e : new ApiError(0, "ERROR", "Something went wrong."));
    } finally { setLoading(false); }
  }, [path, key]);

  useEffect(() => { load(false); }, [load]);
  return { data: result?.data ?? null, at: result?.at ?? null, error, loading, refresh: () => load(true) };
}

export function useApi<T = any>(path: string | null, params?: Params) {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<ApiError | null>(null);
  const [loading, setLoading] = useState<boolean>(path !== null);
  const key = JSON.stringify(params ?? {});

  const load = useCallback(async () => {
    if (path === null) return;
    setLoading(true);
    setError(null);
    try {
      setData(await api<T>(path, { params: JSON.parse(key) }));
    } catch (e) {
      setError(e instanceof ApiError ? e : new ApiError(0, "ERROR", "Something went wrong."));
    } finally {
      setLoading(false);
    }
  }, [path, key]);

  useEffect(() => { load(); }, [load]);
  return { data, error, loading, reload: load, setData };
}
