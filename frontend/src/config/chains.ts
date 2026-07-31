/**
 * Chain-agnostic EVM chain registry for the frontend.
 *
 * Mirrors `backend/app/core/chains.py`. Adding a new chain here (plus its
 * wagmi chain import) is the only change needed to support it end-to-end —
 * no component should ever branch on a hardcoded chain ID.
 */
import {
  arbitrum,
  avalanche,
  base,
  bsc,
  mainnet,
  optimism,
  polygon,
} from "wagmi/chains";
import type { Chain } from "viem";

export const SUPPORTED_CHAINS: readonly [Chain, ...Chain[]] = [
  mainnet,
  bsc,
  polygon,
  base,
  arbitrum,
  optimism,
  avalanche,
];

export function isSupportedChain(chainId: number): boolean {
  return SUPPORTED_CHAINS.some((chain) => chain.id === chainId);
}

export function getChain(chainId: number): Chain | undefined {
  return SUPPORTED_CHAINS.find((chain) => chain.id === chainId);
}
