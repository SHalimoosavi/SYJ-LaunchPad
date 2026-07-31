"""Chain-agnostic EVM chain registry.

Adding a new chain is a data change here (plus an RPC_URL_<id> env var), never
a code change elsewhere in the app. Every module that needs chain metadata
(name, native currency, explorer) reads it from here rather than hardcoding.
"""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ChainInfo:
    chain_id: int
    name: str
    native_currency_symbol: str
    explorer_url: str
    is_testnet: bool = False


# Canonical metadata for chains SYJ LaunchPad ships support for out of the
# box. `Settings.chain_ids` (from ENABLED_CHAIN_IDS) determines which of
# these are actually active for a given deployment.
SUPPORTED_CHAINS: dict[int, ChainInfo] = {
    1: ChainInfo(1, "Ethereum", "ETH", "https://etherscan.io"),
    56: ChainInfo(56, "BNB Smart Chain", "BNB", "https://bscscan.com"),
    137: ChainInfo(137, "Polygon", "POL", "https://polygonscan.com"),
    8453: ChainInfo(8453, "Base", "ETH", "https://basescan.org"),
    42161: ChainInfo(42161, "Arbitrum One", "ETH", "https://arbiscan.io"),
    10: ChainInfo(10, "Optimism", "ETH", "https://optimistic.etherscan.io"),
    43114: ChainInfo(43114, "Avalanche C-Chain", "AVAX", "https://snowtrace.io"),
    # Testnets
    11155111: ChainInfo(11155111, "Sepolia", "ETH", "https://sepolia.etherscan.io", True),
    97: ChainInfo(97, "BSC Testnet", "tBNB", "https://testnet.bscscan.com", True),
}


def get_chain_info(chain_id: int) -> ChainInfo:
    try:
        return SUPPORTED_CHAINS[chain_id]
    except KeyError as exc:
        raise ValueError(f"Unsupported chain_id: {chain_id}") from exc
