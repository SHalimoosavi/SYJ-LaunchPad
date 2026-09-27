"use client";

import { useAuth } from "@/hooks/useAuth";

import { StatusDot } from "./StatusDot";

function truncateAddress(address: string): string {
  return `${address.slice(0, 6)}…${address.slice(-4)}`;
}

export function UserBadge() {
  const { status, user } = useAuth();

  if (status === "loading") {
    return (
      <span className="flex items-center gap-1.5 text-neutral-500">
        <StatusDot state="pending" />
        Checking session…
      </span>
    );
  }

  if (status !== "authenticated" || !user) {
    return (
      <span className="flex items-center gap-1.5 text-neutral-500">
        <StatusDot state="pending" />
        Not signed in
      </span>
    );
  }

  return (
    <span className="flex items-center gap-1.5 text-neutral-500">
      <StatusDot state="ok" />
      Signed in as{" "}
      <span className="font-mono text-foreground">{truncateAddress(user.walletAddress)}</span>
      <span className="rounded-full border border-neutral-300 px-1.5 py-0.5 text-xs uppercase tracking-wide text-neutral-500 dark:border-neutral-700">
        {user.role}
      </span>
    </span>
  );
}
