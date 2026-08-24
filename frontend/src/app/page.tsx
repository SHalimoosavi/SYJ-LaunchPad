import { ConnectButton } from "@rainbow-me/rainbowkit";

import { ApiStatus } from "@/components/ApiStatus";
import { UserBadge } from "@/components/UserBadge";

export default function HomePage() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center gap-8 p-8">
      <h1 className="text-3xl font-semibold tracking-tight">SYJ LaunchPad</h1>
      <p className="max-w-md text-center text-neutral-500">
        Open-source, self-hosted Web3 token launchpad. Connect a wallet and
        sign in with Ethereum — presale features land in later phases.
      </p>
      <ConnectButton />
      <UserBadge />
      <ApiStatus />
    </main>
  );
}
