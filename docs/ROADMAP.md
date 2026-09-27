# Roadmap

Each phase is a complete, working, tested increment. We never leave a phase
half-implemented — if a phase is marked done, it runs, it's tested, and it's
documented.

- [x] **Phase 1 — Foundation.** Monorepo scaffold, backend app factory +
      config + DB session plumbing, frontend app shell, contracts workspace,
      Docker Compose (Postgres), GitHub Actions CI, environment templates.
- [x] **Phase 2 — Wallet Authentication.** SIWE (EIP-4361) sign-in: nonce
      issuance with persisted, single-use replay protection; full
      cryptographic signature verification (domain, chain, expiry, nonce);
      JWT session issuance; RainbowKit custom authentication adapter wired
      end-to-end on the frontend, with session restore on page load.
- [x] **Phase 3 — Core Data Model.** Normalized schema for Users, Wallets
      (from Phase 2), Projects, Sales, Purchases, Claims, Transactions,
      Whitelist, Referral Rewards, Audit Logs, Notifications, Settings.
      *History note: this phase was first implemented and shipped as
      "Project Registration" — the `Project` entity alone, with a full
      ownership-enforced API (create/list-own/get-own/update-own,
      404-not-403 cross-user isolation) — then extended to the complete
      12-entity Core Data Model. The Project Registration work was kept
      as-is, not rewritten, when the phase's scope was clarified.*
      The remaining 9 entities are schema/migration/persistence-tested
      only — no new API routes, no business logic (sale execution, claim
      settlement, referral payout, etc. are Phase 5–7). Alembic migration
      chain verified upgrade AND full downgrade-to-base AND re-upgrade
      against a genuinely fresh Postgres database. Token/tokenomics/
      presale-execution fields deliberately excluded — Phase 4+.
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
