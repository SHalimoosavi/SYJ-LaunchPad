import { getDefaultConfig } from "@rainbow-me/rainbowkit";
import { SUPPORTED_CHAINS } from "./chains";

const walletConnectProjectId = process.env.NEXT_PUBLIC_WALLETCONNECT_PROJECT_ID;

if (!walletConnectProjectId) {
  // Fail loudly at build/boot time rather than silently breaking wallet
  // connect in production.
  throw new Error(
    "NEXT_PUBLIC_WALLETCONNECT_PROJECT_ID is not set. Get one at https://cloud.walletconnect.com"
  );
}

export const wagmiConfig = getDefaultConfig({
  appName: "SYJ LaunchPad",
  projectId: walletConnectProjectId,
  chains: SUPPORTED_CHAINS,
  ssr: true,
});
