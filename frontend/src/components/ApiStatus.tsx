"use client";

import { useQuery } from "@tanstack/react-query";

import { apiFetch } from "@/lib/api";

import { StatusDot } from "./StatusDot";

interface HealthResponse {
  status: string;
  environment: string;
  database: string;
}

export function ApiStatus() {
  const { data, isLoading, isError } = useQuery({
    queryKey: ["health"],
    queryFn: () => apiFetch<HealthResponse>("/api/v1/health"),
  });

  if (isLoading) {
    return (
      <span className="flex items-center gap-1.5 text-neutral-500">
        <StatusDot state="pending" />
        Checking API…
      </span>
    );
  }

  if (isError || !data) {
    return (
      <span className="flex items-center gap-1.5 text-red-500">
        <StatusDot state="error" />
        API unreachable
      </span>
    );
  }

  return (
    <span className="flex items-center gap-1.5 text-neutral-500">
      <StatusDot state="ok" />
      API {data.status} · {data.environment} · db {data.database}
    </span>
  );
}
