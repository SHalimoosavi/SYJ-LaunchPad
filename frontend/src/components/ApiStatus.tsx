"use client";

import { useQuery } from "@tanstack/react-query";

import { apiFetch } from "@/lib/api";

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
    return <div className="animate-pulse text-sm text-neutral-500">Checking API…</div>;
  }

  if (isError || !data) {
    return <div className="text-sm text-red-500">API unreachable</div>;
  }

  return (
    <div className="text-sm text-neutral-500">
      API: <span className="font-medium text-green-500">{data.status}</span> ·{" "}
      {data.environment} · db: {data.database}
    </div>
  );
}
