import { ConnectButton } from "@rainbow-me/rainbowkit";

import { ApiStatus } from "@/components/ApiStatus";
import { ProjectRegistration } from "@/components/ProjectRegistration";
import { UserBadge } from "@/components/UserBadge";

export default function HomePage() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center gap-8 p-8">
      <h1 className="text-3xl font-semibold tracking-tight">SYJ LaunchPad</h1>
      <p className="max-w-md text-center text-neutral-500">
        Open-source, self-hosted Web3 token launchpad. Connect a wallet and
        sign in with Ethereum to register a project.
      </p>
      <ConnectButton />
      <UserBadge />
      <ProjectRegistration />
      <ApiStatus />
    </main>
  );
}
