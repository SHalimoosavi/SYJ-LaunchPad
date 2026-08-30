# Contracts

Hardhat **and** Foundry workspace for SYJ LaunchPad's on-chain contracts.
See [../docs/CONTRACTS_TOOLCHAIN.md](../docs/CONTRACTS_TOOLCHAIN.md) for
full setup, validation commands, and the Slither integration's documented
limitation against an empty `src/`.

**Status:** tooling only — `src/` is intentionally empty. Financial
contract source (ERC20 template, Presale, Treasury, Claim, Vesting,
Referral) is blocked pending explicit approval of target chain, tokenomics,
presale/vesting parameters, and treasury/admin architecture — see the
"Blocked" section in the toolchain doc. We're not shipping placeholder/toy
contracts ahead of that: a presale or vesting contract handles other
people's money, so it gets designed, written, and tested as one coherent
unit once its actual parameters are known — not stubbed out now and
patched later.

## Quick start

```bash
npm install
npx hardhat compile && npx hardhat test

foundryup && npm run forge:install
npm run forge:build && npm run forge:test

pip install slither-analyzer && npm run slither
```

## Networks

Configured networks live in `hardhat.config.ts`, keyed by RPC URL env vars
(`RPC_URL_<chainId>`) — see `.env.example`. Adding a new EVM chain is a
config change, never a code change, matching the chain registries in
`backend/app/core/chains.py` and `frontend/src/config/chains.ts`.
No target deployment chain has been selected yet — see
[../docs/CONTRACTS_TOOLCHAIN.md](../docs/CONTRACTS_TOOLCHAIN.md).
