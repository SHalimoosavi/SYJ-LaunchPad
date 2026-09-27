"use client";

import { useMemo } from "react";
import { createAuthenticationAdapter } from "@rainbow-me/rainbowkit";
import { createSiweMessage } from "viem/siwe";

import { ApiError, apiFetch } from "@/lib/api";
import { type AuthUser, useAuth } from "@/hooks/useAuth";

interface NonceResponse {
  nonce: string;
}

interface VerifyResponse {
  access_token: string;
  user: { id: string; wallet_address: string; role: string };
}

/**
 * Wires RainbowKit's sign-in-with-wallet UI to our backend's
 * `/auth/nonce` -> `/auth/verify` flow (see backend/app/features/auth).
 *
 * `domain`/`uri` here must match `SIWE_DOMAIN`/`SIWE_URI` on the backend —
 * that match is exactly the phishing defense SIWE's domain-binding
 * provides, so a mismatch is a config bug, not a UI bug.
 */
export function useSiweAuthenticationAdapter() {
  const { login, logout } = useAuth();

  return useMemo(
    () =>
      createAuthenticationAdapter({
        getNonce: async () => {
          const { nonce } = await apiFetch<NonceResponse>("/api/v1/auth/nonce");
          return nonce;
        },

        createMessage: ({ nonce, address, chainId }) =>
          createSiweMessage({
            domain: window.location.host,
            address,
            statement: "Sign in to SYJ LaunchPad.",
            uri: window.location.origin,
            version: "1",
            chainId,
            nonce,
          }),

        verify: async ({ message, signature }) => {
          try {
            const result = await apiFetch<VerifyResponse>("/api/v1/auth/verify", {
              method: "POST",
              body: JSON.stringify({ message, signature }),
            });
            const user: AuthUser = {
              id: result.user.id,
              walletAddress: result.user.wallet_address,
              role: result.user.role,
            };
            login(result.access_token, user);
            return true;
          } catch (error) {
            if (error instanceof ApiError) {
              console.error("SIWE verification failed:", error.code, error.message);
            }
            return false;
          }
        },

        signOut: async () => {
          logout();
        },
      }),
    [login, logout]
  );
}
