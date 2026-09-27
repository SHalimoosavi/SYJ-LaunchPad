/**
 * Access-token persistence.
 *
 * Trade-off, documented rather than silent: we store the JWT in
 * localStorage so a page refresh doesn't force a new wallet signature.
 * localStorage is readable by any script on the page, so an XSS
 * vulnerability elsewhere in the app could exfiltrate the token — the
 * mitigations are (1) tokens are short-lived (see
 * ACCESS_TOKEN_EXPIRE_MINUTES on the backend, default 60 min), (2) the
 * token carries no secret beyond "this wallet is signed in", and (3) this
 * app sets a strict CSP (see next.config.ts) to reduce XSS surface in the
 * first place. An httpOnly cookie would close this gap entirely but
 * requires the frontend and backend to share a domain (or SameSite=None
 * cookies across Vercel/Railway), which is a bigger infra decision — worth
 * revisiting in Phase 10 (hardening) if the product needs it.
 */

const TOKEN_KEY = "syj_access_token";

export function getStoredToken(): string | null {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem(TOKEN_KEY);
}

export function setStoredToken(token: string): void {
  window.localStorage.setItem(TOKEN_KEY, token);
}

export function clearStoredToken(): void {
  window.localStorage.removeItem(TOKEN_KEY);
}
