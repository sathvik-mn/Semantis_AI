# AGENTS.md

## Cursor Cloud specific instructions

### Project overview

Semantis AI is a semantic caching platform for LLM applications with two main services:

- **Backend** (`backend/`): FastAPI server on port 8000. See `backend/README.md` for API details.
- **Frontend** (`frontend/`): React + Vite + Tailwind dashboard on port 3000. See `frontend/README.md` for details.

### Running services

**Backend:**
```bash
cd backend && source .venv/bin/activate && python semantic_cache_server.py
```

**Frontend:**
```bash
cd frontend && npm run dev
```

### Key caveats

- The backend requires `python3.12-venv` system package to create the virtual environment. The update script handles venv creation.
- The backend starts successfully **without** Redis, Supabase, or OpenAI keys -- it gracefully degrades to in-memory caching and prints warnings. Query endpoints requiring OpenAI will fail without `OPENAI_API_KEY`.
- The frontend needs `VITE_SUPABASE_URL` and `VITE_SUPABASE_ANON_KEY` in `frontend/.env` (even placeholder values) or the page will render blank. Placeholder values are sufficient for viewing the UI; actual Supabase credentials are needed for auth flows.
- `.env` files for backend and frontend are git-ignored; they must be created from `.env.example` templates.
- No ESLint or Python linter is configured. Use `npx tsc --noEmit` in `frontend/` for TypeScript checking and `npx vite build` for build validation.
- Pre-existing TypeScript errors exist (unused variables, a minor supabase config type issue) but do not block the Vite build.
- Backend tests in `backend/test_api.py` require the backend server to be running on port 8000 and work best with a valid `OPENAI_API_KEY`.
