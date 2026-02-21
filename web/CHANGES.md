# CHANGES

## Phase 1 — Critical bug fixes

### `src/middleware.ts`
- Added redirect from `/app/onboarding` → `/onboarding` (legacy path)
- Added public routes: `/simulate/invite/(.*)`, `/profile/(.*)`, `/api/shadow-vector/(.*)`

### `src/components/onboarding/CompletionScreen.tsx` (full rewrite)
- **Auto-saves shadow vector on mount** via `useEffect` — data is persisted before user clicks any button, eliminating data loss if the network call times out or fails
- Removed the generic "Something went wrong. Please try again." error — save failures are shown as a non-blocking soft warning
- Button now says "Invite someone to simulate →" and opens an inline invite panel (Phase 2)
- Added WhatsApp share with pre-filled attachment-style message (Phase 5)

### `src/app/(app)/dashboard/simulations/page.tsx`
- Fixed infinite spinner when `userId` is undefined after Clerk loads (now shows demo data immediately)

### `src/app/api/webhooks/clerk/route.ts`
- Fixed welcome email link: `/app/onboarding` → `/onboarding`

---

## Phase 2 — Two-sided invite loop

### `src/app/simulate/invite/[token]/page.tsx` (new)
- Public invite landing page at `/simulate/invite/[token]`
- Not signed in → prompts sign-up with redirect back to invite
- Signed in, no shadow vector → prompts onboarding (token persisted in `localStorage`)
- Signed in with shadow vector → shows "Run the simulation" CTA, claims invite, redirects to live simulation viewer
- Stores invite token in `localStorage` under key `prelude_pending_invite` so post-onboarding flow can auto-claim

### `src/lib/api.ts`
- Added `createInvite`, `getInviteInfo`, `claimInvite` API client functions

---

## Phase 3 — Shadow Vector identity card

### `src/app/api/shadow-vector/card/[userId]/route.tsx` (new)
- Edge runtime OG image generator using `next/og`
- Returns 1200×630 PNG (OG) or 1080×1080 (Instagram square via `?format=square`)
- Shows top 3 ranked values, attachment style label + one-line read-out, PRELUDE branding

### `src/app/(marketing)/profile/[username]/page.tsx` (new)
- Public profile page at `/profile/[userId]`
- Shows shadow vector card preview
- Download PNG, Share on WhatsApp buttons
- CTA to build your own profile on PRELUDE

### `src/app/(app)/dashboard/profile/page.tsx`
- Added "View public card" link (opens `/profile/[userId]`)
- Added "Share your Shadow Vector on WhatsApp" button with pre-filled message

---

## Phase 4 — Waitlist improvements

### `src/app/(marketing)/match/page.tsx`
- Replaced Indian-cities `<select>` dropdown with free-text `<input type="text">` for city field
- Removed `cities` array — accepts any city worldwide

### `apriori/api/routes/waitlist.py`
- Added `_send_waitlist_email()` — sends Resend confirmation with position, referral code, share link
- Email fires as a background task (non-blocking)
- Referral advancement: referrer moves up 50 positions, referee also gets −50 from their initial position (both min 1)

---

## Phase 5 — WhatsApp sharing

### `src/components/report/SimulationReport.tsx`
- Added "Share on WhatsApp" button in the report header
- Pre-filled message includes homeostasis rate, top tension pattern, and link to `/match`

### `src/components/onboarding/CompletionScreen.tsx`
- WhatsApp share button in invite panel: "I just found out I'm [attachment label] on PRELUDE…"

---

## Backend

### `apriori/db/models.py`
- Added `SimulationInvite` model with fields: `token`, `inviter_user_id`, `invitee_user_id`, `status`, `expires_at`, `simulation_run_id`

### `alembic/versions/002_simulation_invites.py` (new)
- Migration creating `simulation_invites` table

### `apriori/api/routes/invites.py` (new)
- `POST /invites` — creates 12-char token, 72-hour expiry (auth required)
- `GET /invites/{token}` — public; returns status, inviter attachment style
- `POST /invites/{token}/claim` — pairs invitee + inviter, launches 20-timeline background simulation

### `apriori/api/main.py`
- Registered `/invites` router

### `apriori/api/routes/auth.py`
- `/auth/me` now auto-creates `UserProfile` from JWT claims if not found (webhook fallback)

### `apriori/pyproject.toml`
- Added `httpx>=0.27.0` to main dependencies (used for Resend emails)
