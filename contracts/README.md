# Contracts

Hardhat workspace for SYJ LaunchPad's on-chain contracts.

**Status:** tooling only. Contract source lands in Phase 4 (see
[../docs/ROADMAP.md](../docs/ROADMAP.md)) — ERC20 template, Presale, Treasury,
Claim, Vesting, Referral, with full Foundry + Hardhat test suites and Slither
static analysis wired into CI.

We're not shipping placeholder/toy contracts ahead of that phase: a presale
or vesting contract handles other people's money, so it gets designed,
written, and tested as one coherent unit — not stubbed out now and patched
later.

## Local dev (once contracts exist)

```bash
npm install
npx hardhat compile
npx hardhat test
npx hardhat coverage
```

## Networks

Configured networks live in `hardhat.config.ts`, keyed by RPC URL env vars
(`RPC_URL_<chainId>`) — see `.env.example`. Adding a new EVM chain is a
config change, never a code change, matching the chain registries in
`backend/app/core/chains.py` and `frontend/src/config/chains.ts`.
