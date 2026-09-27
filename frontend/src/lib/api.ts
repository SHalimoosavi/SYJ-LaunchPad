/**
 * Thin typed fetch wrapper around the backend API.
 *
 * Every backend error follows the envelope
 *   { error: { code, message, details } }
 * (see backend/app/common/errors.py) — `ApiError` below mirrors that shape
 * so callers get a typed, catchable error instead of a raw Response.
 */

import { getStoredToken } from "./token-storage";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export class ApiError extends Error {
  constructor(
    public readonly code: string,
    message: string,
    public readonly status: number,
    public readonly details: Record<string, unknown> = {}
  ) {
    super(message);
    this.name = "ApiError";
  }
}

interface ErrorEnvelope {
  error: { code: string; message: string; details?: Record<string, unknown> };
}

export async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const token = getStoredToken();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(init?.headers as Record<string, string> | undefined),
  };
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers,
  });

  if (!response.ok) {
    let body: ErrorEnvelope | null = null;
    try {
      body = (await response.json()) as ErrorEnvelope;
    } catch {
      // response wasn't JSON — fall through to generic error below
    }
    if (body?.error) {
      throw new ApiError(body.error.code, body.error.message, response.status, body.error.details);
    }
    throw new ApiError("UNKNOWN_ERROR", response.statusText, response.status);
  }

  return response.json() as Promise<T>;
}
