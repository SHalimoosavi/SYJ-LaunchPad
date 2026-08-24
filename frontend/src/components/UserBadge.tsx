"use client";

import { useAuth } from "@/hooks/useAuth";

function truncateAddress(address: string): string {
  return `${address.slice(0, 6)}…${address.slice(-4)}`;
}

export function UserBadge() {
  const { status, user } = useAuth();

  if (status === "loading") {
    return <div className="animate-pulse text-sm text-neutral-500">Checking session…</div>;
  }

  if (status !== "authenticated" || !user) {
    return <div className="text-sm text-neutral-500">Not signed in</div>;
  }

  return (
    <div className="text-sm text-neutral-500">
      Signed in as{" "}
      <span className="font-medium text-foreground">{truncateAddress(user.walletAddress)}</span>{" "}
      · {user.role}
    </div>
  );
}
