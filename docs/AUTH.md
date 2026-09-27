# Wallet Authentication (Phase 2)

Sign-In with Ethereum (EIP-4361), end to end.

## Flow

1. **Frontend** connects a wallet via RainbowKit. RainbowKit's authentication
   UI calls our custom adapter (`frontend/src/config/auth-adapter.ts`).
2. Adapter calls `GET /api/v1/auth/nonce` → backend generates and persists a
   single-use nonce (`SiweNonce`, TTL = `SIWE_NONCE_TTL_SECONDS`).
3. Adapter builds an EIP-4361 message via `createSiweMessage` (viem) and asks
   the wallet to sign it.
4. Adapter calls `POST /api/v1/auth/verify` with `{ message, signature }`.
   Backend (`backend/app/features/auth/service.py`):
   - Parses the message with the `siwe` library.
   - Verifies the signature, domain, and expiry.
   - Checks `chain_id` is one of `ENABLED_CHAIN_IDS`.
   - Burns the nonce (replay protection) — only after signature verification
     succeeds, so a forged message can never burn a legitimate nonce.
   - Finds or creates a `User` + `Wallet` for the signing address.
   - Issues a JWT access token.
5. Frontend stores the token (see trade-off note in
   `frontend/src/lib/token-storage.ts`) and calls `GET /api/v1/auth/me` on
   every future page load to restore the session.

## Security properties this gives you

- **Replay protection**: nonces are persisted (not in-memory), single-use,
  and time-boxed. A captured signature can't be replayed later or against
  a different backend instance.
- **Phishing resistance**: SIWE's `domain` binding means a message signed
  for `SIWE_DOMAIN` can't be replayed against a different site pretending
  to be SYJ LaunchPad.
- **No spoofed wallets**: the signature is cryptographically recovered and
  compared to the claimed address — you cannot claim to be a wallet you
  don't hold the key for.
- **Chain-agnostic**: any chain in `ENABLED_CHAIN_IDS` works out of the box;
  unlisted chains are rejected.

## Extending this in later phases

- `require_role(UserRole.ADMIN)` (in `dependencies.py`) is the hook for
  Phase 8's admin routes.
- Linking a second wallet to an existing user isn't implemented yet — the
  service function `verify_siwe_and_get_user` always resolves to the user
  owning that exact address. A "link wallet" flow would reuse the same
  verification logic but attach the wallet to the *current* authenticated
  user instead of creating a new one.
