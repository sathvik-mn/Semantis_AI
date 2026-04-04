# Semantys AI — Frontend & User Flows

## Tech Stack

- **React 19** with TypeScript, built with **Vite 7**
- **React Router DOM v7** for routing
- **Tailwind CSS v3** for styling
- **Supabase JS v2** for authentication
- **Recharts** for admin dashboard charts
- **Three.js** for animated 3D backgrounds (landing page)
- **Framer Motion** for animations
- **react-markdown + react-syntax-highlighter** for chat message rendering
- **PostHog** for product analytics, **Sentry** for error tracking

---

## All Pages & Routes

### Public Routes (no auth required)

| Route | Component | Description |
|-------|-----------|-------------|
| `/` | `LandingPage` | Marketing homepage with Three.js animated background, hero section ("Cut LLM Costs by 80%"), links to Docs/Pricing/Sign Up |
| `/signin` | `SignInPage` | Email + password login; shows "continue as" if already logged in; redirects to `/playground` on success |
| `/login` | redirect | Alias → `/signin` |
| `/signup` | `SignUpPage` | Registration with real-time password strength checker (8 chars, letter, number); shows email verification prompt |
| `/forgot-password` | `ForgotPasswordPage` | Email input → Supabase `resetPasswordForEmail` |
| `/reset-password` | `ResetPasswordPage` | New password form → Supabase `updateUser` |
| `/pricing` | `PricingPage` | Three-tier pricing cards: Free ($0), Pro ($49/mo), Team (contact) |
| `/docs` | `DocsPage` | Full documentation page |
| `/status` | `StatusPage` | Service status |
| `/security` | `SecurityPage` | Security information |
| `/privacy` | `PrivacyPage` | Privacy policy |
| `*` | `NotFoundPage` | 404 fallback |

### Protected Routes (require login)

All wrapped in `ProtectedRoute` → redirects to `/signin` if not authenticated.

| Route | Component | Description |
|-------|-----------|-------------|
| `/playground` | `PlaygroundPage` | Main chat interface with SSE streaming, cache hit badges, history panel |
| `/home` | redirect | Alias → `/playground` |
| `/metrics` | `MetricsPage` | KPI cards, savings dashboard, insight cards, auto-refresh every 15s |
| `/logs` | `LogsPage` | Sortable/filterable event log table, CSV download, auto-refresh every 10s |
| `/settings` | `SettingsPage` | Billing section + settings panel (API key, BYOK, threshold, TTL, warmup) |

### Admin Routes (require `is_admin = true`)

| Route | Component | Description |
|-------|-----------|-------------|
| `/admin/login` | `AdminLoginPage` | Admin-specific login (checks `is_admin` flag) |
| `/admin` | `AdminDashboard` | KPI cards, growth/usage charts, plan distribution, configurable time window |
| `/admin/users` | `AdminUsers` | Paginated user list, search, per-user details, plan change, activate/deactivate |
| `/admin/top-users` | `AdminTopUsers` | Ranked user table (by requests, hits, tokens, savings) |
| `/admin/analytics` | `AdminAnalytics` | Platform-wide analytics charts |
| `/admin/settings` | `AdminSettings` | System health page |

---

## Authentication Flow

Authentication is entirely **Supabase-based** using PKCE flow.

### Sign Up
```
1. User fills email + password on /signup
2. supabase.auth.signUp() called
3. Supabase sends verification email
4. User clicks link → email verified
5. User can now sign in
```

### Sign In
```
1. User enters email + password on /signin
2. supabase.auth.signInWithPassword()
3. JWT stored in localStorage (sb-auth-token)
4. AuthContext enriches user via GET /api/auth/me (fetches name, is_admin)
5. API key loaded via GET /api/keys/current → stored in localStorage (semantic_api_key)
6. Redirect to /playground
```

### Session Management
- `AuthContext` wraps the entire app
- On mount: calls `supabase.auth.getSession()` with 3-second timeout
- `supabase.auth.onAuthStateChange` subscription re-enriches user on token refresh
- Tokens stored in `localStorage` under `sb-auth-token`

### Password Reset
```
1. /forgot-password → supabase.auth.resetPasswordForEmail(email, redirectTo: /reset-password)
2. User clicks email link → lands on /reset-password
3. supabase.auth.updateUser({ password: newPassword })
```

---

## Frontend ↔ Backend Communication

Two API modules, both pointing to `VITE_BACKEND_URL`:

### Main API (`api/semanticAPI.ts`) — native `fetch`

**Pattern 1 — API Key Bearer** (cache/metrics/settings endpoints):
- API key (`sc-{tenant}-{...}`) stored in `localStorage` as `semantic_api_key`
- Sent as `Authorization: Bearer {apiKey}`
- Used for: `/v1/chat/completions`, `/metrics`, `/events`, `/settings`

**Pattern 2 — Supabase JWT Bearer** (account/billing endpoints):
- Fresh access token from `supabase.auth.getSession()`
- Used for: `/api/keys/*`, `/api/users/*`, `/api/billing/*`, `/api/credits/*`, `/api/cache/*`, `/api/auth/*`

**SSE Streaming**: `sendChatCompletionStream()` is an async generator that reads Server-Sent Events from `/v1/chat/completions` (with `stream: true`), parsing `data: {...}` lines and yielding content deltas in real time.

### Admin API (`api/adminAPI.ts`) — Axios

- Axios instance with `baseURL = /admin`
- Request interceptor injects Supabase JWT into every request
- Backend validates `is_admin` from the JWT

---

## Key Components

### Chat & Playground
| Component | Purpose |
|-----------|---------|
| `QueryPlayground` | Full chat UI: SSE streaming, markdown rendering, per-message cache badges (EXACT/SEMANTIC/MISS with latency, similarity %, token count), history panel (50 entries in localStorage), model selector, temperature slider |
| `MarkdownRenderer` | Memoized react-markdown with syntax-highlighted code blocks (Prism oneDark theme) and copy button |

### Settings & Billing
| Component | Purpose |
|-----------|---------|
| `SettingsPanel` | API key generate/copy, BYOK OpenAI key save/remove (validates `sk-` prefix), similarity threshold slider (0.50–0.99), TTL input (1–90 days) |
| `BillingSection` | Current plan, monthly usage progress bar, BYOK indicator, credits balance with low-credit warning, upgrade buttons, Stripe portal link |
| `CacheWarmup` | Upload JSONL/JSON or paste JSON array of `{prompt, response, model}` entries; submits in batches of 50 |

### Metrics & Logs
| Component | Purpose |
|-----------|---------|
| `KpiCards` | Five metric cards: Hit Ratio, Semantic Hit Ratio, Avg Latency, Total Requests, Tokens Saved |
| `SavingsDashboard` | 30-day savings stats: cached requests, hit rate, estimated USD saved, tokens saved |
| `LogsTable` | Sortable table of cache events (timestamp, decision badge, similarity %, latency, prompt hash), CSV download |

### Layout & Navigation
| Component | Purpose |
|-----------|---------|
| `Layout` | Persistent shell: sticky top nav with health indicator (polls `/health` every 30s), nav links, account menu, footer |
| `AdminLayout` | Admin shell: fixed left sidebar, dark/light mode toggle (persisted to localStorage), "Back to App" link |
| `OnboardingWizard` | 4-step modal for new users: Welcome → Get API Key → Try Playground → View Metrics |

### Visual
| Component | Purpose |
|-----------|---------|
| `TubesBackground` | Three.js animated tube/particle background (landing, sign-in, sign-up pages) |
| `LightRays` | Canvas-based animated light rays (protected app pages) |
| `ErrorBoundary` | Catches render errors, shows fallback error screen |

---

## Custom Hooks

| Hook | Purpose |
|------|---------|
| `useSemanticCache()` | Wraps `sendChatCompletion` with loading/error state |
| `useMetrics(refreshInterval?)` | Fetches `/metrics` on interval; only runs if API key is present |
| `useEvents(limit, refreshInterval?)` | Fetches `/events?limit=N` on interval |
| `useHealthCheck(intervalMs)` | Polls `/health`; returns `true/false/null` |

---

## User Journey

### New User
```
1. Land on / (marketing page)
2. Click "Get Started" → /signup
3. Enter email + password → verify email
4. Sign in → /playground
5. OnboardingWizard appears (4 steps):
   a. Welcome message
   b. API key is auto-generated
   c. Try the playground (send a query)
   d. View metrics
6. User starts using playground — sees cache hits on repeated queries
7. Explore /metrics for savings dashboard
8. Explore /settings to adjust threshold or add BYOK key
```

### Returning User
```
1. /signin → email + password
2. → /playground (API key loaded from localStorage/backend)
3. Full access to playground, metrics, logs, settings
```

### Admin User
```
1. /admin/login → email + password (must have is_admin = true)
2. → /admin dashboard with KPI cards and charts
3. Navigate sidebar: Users, Top Users, Analytics, Settings
4. Can change plans, activate/deactivate users, view audit logs
```

---

## Environment Variables

| Variable | Purpose |
|----------|---------|
| `VITE_BACKEND_URL` | Backend API base URL (default: `http://localhost:8000`) |
| `VITE_SUPABASE_URL` | Supabase project URL |
| `VITE_SUPABASE_ANON_KEY` | Supabase anonymous/public key |
| `VITE_SENTRY_DSN` | Sentry DSN for error tracking (optional) |
| `VITE_POSTHOG_KEY` | PostHog project key for analytics (optional) |
| `VITE_POSTHOG_HOST` | PostHog ingest host |
