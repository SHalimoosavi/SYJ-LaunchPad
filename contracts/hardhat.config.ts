import "@nomicfoundation/hardhat-toolbox";
import type { HardhatUserConfig } from "hardhat/config";
import * as dotenv from "dotenv";

dotenv.config();

const DEPLOYER_KEY = process.env.DEPLOYER_PRIVATE_KEY;
const accounts = DEPLOYER_KEY ? [DEPLOYER_KEY] : [];

/**
 * Chain-agnostic network registry, mirroring backend/app/core/chains.py and
 * frontend/src/config/chains.ts. Adding a new chain is a new entry here plus
 * an RPC_URL_<name> env var — never a code change.
 */
const config: HardhatUserConfig = {
  solidity: {
    version: "0.8.28",
    settings: {
      optimizer: { enabled: true, runs: 200 },
      evmVersion: "paris",
    },
  },
  networks: {
    hardhat: {},
    ethereum: { url: process.env.RPC_URL_1 ?? "", chainId: 1, accounts },
    bsc: { url: process.env.RPC_URL_56 ?? "", chainId: 56, accounts },
    polygon: { url: process.env.RPC_URL_137 ?? "", chainId: 137, accounts },
    base: { url: process.env.RPC_URL_8453 ?? "", chainId: 8453, accounts },
    arbitrum: { url: process.env.RPC_URL_42161 ?? "", chainId: 42161, accounts },
    optimism: { url: process.env.RPC_URL_10 ?? "", chainId: 10, accounts },
    avalanche: { url: process.env.RPC_URL_43114 ?? "", chainId: 43114, accounts },
    sepolia: { url: process.env.RPC_URL_11155111 ?? "", chainId: 11155111, accounts },
    bscTestnet: { url: process.env.RPC_URL_97 ?? "", chainId: 97, accounts },
  },
  etherscan: {
    apiKey: {
      mainnet: process.env.ETHERSCAN_API_KEY ?? "",
      bsc: process.env.BSCSCAN_API_KEY ?? "",
      polygon: process.env.POLYGONSCAN_API_KEY ?? "",
    },
  },
  paths: {
    sources: "./src",
    tests: "./test",
    cache: "./cache",
    artifacts: "./artifacts",
  },
};

export default config;
