# SYJ LaunchPad

Open-source, self-hosted Web3 token launchpad. Deploy your own presale/IDO
platform from your own website — no third-party launchpad, no platform fees.

> **Status:** Phase 1 — foundational architecture. See [docs/ROADMAP.md](docs/ROADMAP.md).

## Monorepo Layout

```
syj-launchpad/
├── backend/         FastAPI service (Python, feature-based architecture)
├── frontend/         Next.js 15 app (App Router, TypeScript, Tailwind, wagmi)
├── contracts/        Hardhat workspace (Solidity, OpenZeppelin)
├── docs/              Architecture, deployment, and decision records
└── .github/workflows  CI (lint, type-check, test, build)
```

## Why this structure

- **Feature-based, not layer-based.** Each domain (auth, presale, claim, vesting,
  referral, admin...) owns its own routes/schemas/models/services/tests on the
  backend, and its own components/hooks/types on the frontend. This keeps the
  codebase scalable as the platform grows into IDO/NFT/DAO/staking modules
  without a rewrite.
- **Chain-agnostic by design.** No chain ID, RPC URL, or contract address is
  hardcoded anywhere. Chains are configuration (`backend/app/core/chains.py` +
  `frontend/src/config/chains.ts`), so adding a new EVM chain is a config
  change, not a code change.
- **Contracts are immutable by default.** Upgradeable proxies add real
  complexity and a real attack surface (storage collisions, admin key risk).
  We only reach for upgradeability on a specific contract if a documented
  requirement demands it. Everything else ships as simple, audited-once,
  immutable contracts plus a versioned deployment registry.

## Quick start (local dev)

Requirements: Node 20+, Python 3.12+, and Postgres — either via Docker or a
native install. **Database setup is a required first step and is not
optional** — see [docs/DATABASE_SETUP.md](docs/DATABASE_SETUP.md) for exact,
tested commands for both paths (Docker and native Windows/macOS/Linux). The
short version, if you're using Docker:

```bash
cp .env.example .env
docker compose up -d          # postgres — creates the syj/syj_launchpad db automatically
cd backend && cp .env.example .env && pip install -e ".[dev]"
alembic upgrade head
uvicorn app.main:app --reload

# separate terminal
cd frontend && npm install && npm run dev

# separate terminal (contracts)
cd contracts && npm install && npx hardhat test
```

## Deployment (₹0 baseline)

- Frontend → Vercel (free tier)
- Backend → Railway
- Database → Railway PostgreSQL
- CI/CD → GitHub Actions
- Domain → Vercel subdomain initially

See [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) for step-by-step instructions and
the upgrade path to Docker/Kubernetes/AWS/GCP/Azure/self-hosted.

## Documented assumptions (Phase 1)

Where the spec didn't pin an exact version or the pinned version wasn't
available in this environment, we made an explicit, documented call rather
than guessing silently:

| Item | Spec said | We used | Why |
|---|---|---|---|
| Python | 3.13 | **3.12** minimum, 3.13-compatible | 3.12 is what's verified in this dev environment; codebase avoids any 3.13-only syntax so it runs on either. |
| Next.js | 16 | **15 (App Router)** | 16 is not yet GA on npm as of this writing; pinning to a real, installable major avoids a broken `npm install` on day one. Upgrading later is a one-line bump. |
| Repository Pattern | "only if it simplifies" | **Not used** | SQLAlchemy 2 async sessions + a thin service layer already give us testability (session can be mocked/faked) without an extra abstraction layer. |

These will be revisited if requirements change; nothing here blocks upgrading
once the newer toolchain is available.
