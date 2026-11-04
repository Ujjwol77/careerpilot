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
  clear: () => { try { window.localStorage.removeItem(KEY); } catch { /* storage unavailable */ } },
};

export class ApiError extends Error {
  constructor(public status: number, public code: string, message: string) {
    super(message);
  }
}

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

// eslint-disable-next-line @typescript-eslint/no-explicit-any
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
