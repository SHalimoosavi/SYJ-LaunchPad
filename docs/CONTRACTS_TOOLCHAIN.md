# Contracts Toolchain

**Status: tooling only.** No financial contract source exists in this
repository (`contracts/src/` is empty). This is deliberate, not an
oversight — see [Blocked](#blocked-pending-authoritative-parameters) below.

## Two toolchains, one source tree

This project uses **both** Hardhat and Foundry, per `docs/ROADMAP.md`'s
Phase 4 requirement ("Foundry + Hardhat test suites"). They share the same
contract source (`src/`) and test directory (`test/` — Foundry's `.t.sol`
files and Hardhat's `.ts` files coexist there without collision), but keep
separate build-artifact directories so neither tool's cache clobbers the
other's:

| | Hardhat | Foundry |
|---|---|---|
| Source | `src/` | `src/` (same) |
| Tests | `test/` | `test/` (same) |
| Build output | `artifacts/` | `out/` |
| Cache | `cache/` | `cache-forge/` |
| Dependencies | `node_modules/` (npm) | `lib/` (git-free `forge install`) |

## Local setup

```bash
cd contracts
npm install                    # Hardhat + OpenZeppelin + tooling

curl -L https://raw.githubusercontent.com/foundry-rs/foundryup/HEAD/foundryup-init.sh | bash
export PATH="$PATH:$HOME/.foundry/bin"
foundryup                      # installs forge, cast, anvil

npm run forge:install          # fetches forge-std into lib/ (not committed — see .gitignore)
```

## Local validation

```bash
npm run compile && npm test        # Hardhat
npm run forge:build && npm run forge:test   # Foundry

pip install slither-analyzer
npm run slither                     # see the note below — no-ops cleanly until src/ has contracts
```

## Slither: a real, documented limitation

Slither's Foundry integration (`crytic-compile`) resolves the analysis
target from `foundry.toml`'s `src` path and **fails outright** if that
directory has no `.sol` files — even if `test/` has real contracts.
Reproduced directly:

```
$ slither src/
...
crytic_compile.platform.exceptions.InvalidCompilation: Compilation failed. Can you run build command?
/contracts/out/build-info is not a directory.
```

This is Slither behaving correctly, not a setup bug — it audits
*application* contracts, and there aren't any yet. The CI step (and the
`npm run slither` script) check whether `src/` actually contains `.sol`
files first; if not, they print a message and exit `0` rather than fail
the build or fabricate a placeholder contract to satisfy the tool. The
moment real contract source lands in `src/`, this step activates itself —
no CI change required.

## Environment note (this sandbox specifically, not CI)

`forge build` normally downloads the solc compiler binary from
`binaries.soliditylang.org` on first use. The sandbox this toolchain was
originally verified in has a restricted outbound domain allowlist that
doesn't include that host, so verification there used a solc binary
fetched instead from GitHub Releases
(`github.com/ethereum/solidity/releases`, an allowed domain) and placed
manually into `~/.svm/<version>/`. **Standard CI runners (GitHub Actions)
have normal outbound internet access and do not need this workaround** —
`forge build` will fetch solc itself the ordinary way there. This note
exists so the discrepancy between "verified in a restricted sandbox" and
"will run in CI" is explicit, not silently glossed over.

## Blocked pending authoritative parameters

Per the Phase 4 Checkpoint 0 gate, the following are explicitly
**UNKNOWN** and must not be guessed at by writing contract code around
them:

- Target deployment chain(s)
- Token name, symbol, decimals, total supply, mint/burn policy
- Presale currency, pricing model, soft/hard cap, whitelist policy
- Vesting schedule parameters
- Treasury/admin architecture (multisig? timelock? single EOA?)
- Upgradeability policy per contract

No ERC20, Presale, Treasury, Claim, Vesting, or Referral contract will be
implemented until these are explicitly established. This document and
`contracts/README.md` are updated to reflect that; nothing here claims
financial-contract readiness.
