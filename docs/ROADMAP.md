# Roadmap

Each phase is a complete, working, tested increment. We never leave a phase
half-implemented — if a phase is marked done, it runs, it's tested, and it's
documented.

- [x] **Phase 1 — Foundation.** Monorepo scaffold, backend app factory +
      config + DB session plumbing, frontend app shell, contracts workspace,
      Docker Compose (Postgres), GitHub Actions CI, environment templates.
- [ ] **Phase 2 — Wallet Authentication.** SIWE-style (EIP-4361) signature
      auth, nonce issuance + replay protection, JWT session issuance,
      wagmi/RainbowKit wallet connect on the frontend.
- [ ] **Phase 3 — Core Data Model.** Users, Wallets, Projects, Sales,
      Purchases, Claims, Transactions, Whitelist, Referral Rewards, Audit
      Logs, Notifications, Settings — normalized schema + Alembic migrations.
- [ ] **Phase 4 — Smart Contracts.** ERC20 template, Presale, Treasury, Claim,
      Vesting, Referral, Ownable/Pausable mixins; Foundry + Hardhat test
      suites; static analysis (Slither) in CI.
- [ ] **Phase 5 — Presale Module.** End-to-end: create sale → whitelist →
      public/FCFS sale → purchase → on-chain settlement, wired through
      backend API and frontend flow.
- [ ] **Phase 6 — Claim & Vesting.** Claim schedules, vesting curves, on-chain
      claim verification.
- [ ] **Phase 7 — Referral System.** Referral codes, attribution, reward
      accrual and payout.
- [ ] **Phase 8 — Admin Dashboard.** Sales, projects, whitelist, users,
      analytics, settings, audit logs, treasury, emergency controls, CSV
      export, system health.
- [ ] **Phase 9 — User Dashboard.** Purchases, claimable tokens, vesting
      progress, wallet info, tx history, referral rewards, profile,
      notifications.
- [ ] **Phase 10 — Analytics, Hardening & Docs.** Rate limiting, CSP,
      structured logging/audit trail, load testing, full documentation set,
      security review checklist.

We build phase by phase in this repo's chat thread — say "next phase" and
we continue from here.
