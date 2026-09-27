# Phase 4 Contract Specification

**Status:** Draft -- parameter freeze required before financial contract implementation.

This document defines the architecture and security requirements for the
Phase 4 smart-contract system. It does not authorize deployment and does not
invent tokenomics, chain, pricing, treasury, vesting, or other financial
parameters that have not been explicitly approved.

## 1. Scope

Phase 4 includes:

- ERC20 token template
- Presale contract
- Treasury contract
- Claim contract
- Vesting contract
- Referral contract
- Ownable/Pausable access-control mixins
- Foundry test suite
- Hardhat test suite
- Slither static analysis

## 2. Authoritative Parameters

The following values remain TBD until explicitly approved:

| Parameter | Status |
|---|---|
| Target deployment chain(s) | TBD / BLOCKED |
| Token name | TBD / BLOCKED |
| Token symbol | TBD / BLOCKED |
| Decimals | TBD / BLOCKED |
| Total supply | TBD / BLOCKED |
| Mint policy | TBD / BLOCKED |
| Burn policy | TBD / BLOCKED |
| Presale currency | TBD / BLOCKED |
| Presale price | TBD / BLOCKED |
| Soft cap | TBD / BLOCKED |
| Hard cap | TBD / BLOCKED |
| Minimum contribution | TBD / BLOCKED |
| Maximum contribution | TBD / BLOCKED |
| Whitelist policy | TBD / BLOCKED |
| Sale start/end | TBD / BLOCKED |
| Treasury/admin architecture | TBD / BLOCKED |
| Ownership model | TBD / BLOCKED |
| Pause authority | TBD / BLOCKED |
| Upgradeability policy | TBD / BLOCKED |
| Vesting schedules | TBD / BLOCKED |
| Claim rules | TBD / BLOCKED |
| Referral rules | TBD / BLOCKED |
| Emergency/refund rules | TBD / BLOCKED |

## 3. Contract Architecture

### 3.1 ERC20

Responsibilities:

- Token metadata
- Supply management
- Transfer behavior
- Mint/burn behavior only where explicitly authorized
- Ownership/access control
- Pause behavior only where explicitly required

Security requirements:

- No unrestricted mint authority
- Explicit supply invariant
- Explicit admin authority
- Event coverage for privileged operations
- Foundry fuzz/invariant coverage

### 3.2 Presale

Responsibilities:

- Sale lifecycle
- Eligibility enforcement
- Contribution accounting
- Allocation accounting
- Purchase limits
- Sale close/finalization
- Refund behavior where approved

Security requirements:

- Correct sale window enforcement
- Reentrancy protection where applicable
- No contribution/accounting mismatch
- No allocation overflow
- No unauthorized administrative mutation
- Precise handling of rounding/price calculations
- Fuzz and invariant coverage for money-handling paths

### 3.3 Treasury

Responsibilities:

- Controlled custody/forwarding of treasury assets
- Explicit administrative authorization
- Emergency controls where approved

Security requirements:

- No arbitrary unauthorized withdrawals
- Event emission for asset movement
- Explicit authority model
- Reentrancy protections where applicable

### 3.4 Claim

Responsibilities:

- Claim eligibility
- Claim amount/accounting
- Claimed-state tracking
- Claim execution

Security requirements:

- No double claim
- No unauthorized claim
- Exact accounting
- Proof/signature mechanism only if explicitly approved

### 3.5 Vesting

Responsibilities:

- Beneficiary allocation
- Schedule tracking
- Time-based releasable amount calculation
- Release accounting

Security requirements:

- No over-release
- No double release
- Correct cliff behavior
- Correct linear/non-linear schedule behavior according to approved specification
- Timestamp edge-case testing
- Fuzz/invariant coverage

### 3.6 Referral

Responsibilities:

- Referral attribution
- Reward accounting
- Reward settlement

Security requirements:

- Self-referral handling
- Double attribution prevention
- Reward accounting invariants
- Explicit payout authority
- Event coverage

## 4. Access Control

Each privileged operation must have an explicit authority.

| Operation | Authority |
|---|---|
| Token administration | TBD |
| Mint | TBD |
| Burn | TBD |
| Pause/unpause | TBD |
| Presale configuration | TBD |
| Presale finalization | TBD |
| Treasury withdrawal | TBD |
| Claim administration | TBD |
| Vesting administration | TBD |
| Referral administration | TBD |
| Emergency controls | TBD |
| Upgrade administration | TBD |

## 5. Global Security Requirements

All contracts handling user funds must address:

- Reentrancy
- Integer/rounding correctness
- Access control
- Pause/emergency behavior
- Double-spend/double-claim conditions
- Timestamp boundaries
- Zero-value inputs
- Maximum-value inputs
- State-transition ordering
- Event completeness
- Upgradeability risks where applicable

## 6. Testing Requirements

Every financial contract must have:

### Foundry

- Unit tests
- Negative/revert tests
- Boundary tests
- Fuzz tests
- Invariant tests
- Access-control tests
- Pause/emergency tests
- Accounting conservation tests

### Hardhat

- Deployment/fixture coverage
- Contract interaction regression tests
- Cross-checks against Foundry-tested behavior

### Slither

- Static analysis with findings reviewed
- No ignored high/critical findings without documented disposition

## 7. Completion Gate

Phase 4 implementation is not considered complete until:

- All authoritative parameters are frozen
- Contract interfaces are frozen
- Access-control matrix is frozen
- Financial invariants are documented
- Foundry tests pass
- Hardhat tests pass
- Slither analysis passes or every finding has an explicit documented disposition
- CI is green
- Deployment is not performed until deployment-chain and operational approvals are established

## 8. Change Control

Any change to tokenomics, chain selection, access control, sale mechanics,
vesting mechanics, treasury authority, or upgradeability after this
specification is frozen requires an explicit specification revision before
contract code is changed.
