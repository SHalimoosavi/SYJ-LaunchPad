"use client";

import {
  RainbowKitAuthenticationProvider,
  RainbowKitProvider,
  darkTheme,
  lightTheme,
} from "@rainbow-me/rainbowkit";
import "@rainbow-me/rainbowkit/styles.css";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useState } from "react";
import { WagmiProvider } from "wagmi";

import { useSiweAuthenticationAdapter } from "@/config/auth-adapter";
import { wagmiConfig } from "@/config/wagmi";
import { AuthProvider, useAuth } from "@/hooks/useAuth";

/** Bridges our AuthContext (status/login/logout) into RainbowKit's
 * authentication UI — separated from `Providers` because it needs to be
 * *inside* `AuthProvider` to call `useAuth()`. */
function RainbowKitWithAuth({ children }: { children: React.ReactNode }) {
  const { status } = useAuth();
  const adapter = useSiweAuthenticationAdapter();

  return (
    <RainbowKitAuthenticationProvider adapter={adapter} status={status}>
      <RainbowKitProvider theme={{ lightMode: lightTheme(), darkMode: darkTheme() }}>
        {children}
      </RainbowKitProvider>
    </RainbowKitAuthenticationProvider>
  );
}

export function Providers({ children }: { children: React.ReactNode }) {
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: { queries: { retry: 1, staleTime: 30_000 } },
      })
  );

  return (
    <WagmiProvider config={wagmiConfig}>
      <QueryClientProvider client={queryClient}>
        <AuthProvider>
          <RainbowKitWithAuth>{children}</RainbowKitWithAuth>
        </AuthProvider>
      </QueryClientProvider>
    </WagmiProvider>
  );
}
