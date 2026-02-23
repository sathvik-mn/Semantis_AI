# Semantis AI - Setup Guide

## Prerequisites

- Python 3.11+
- Node.js 18+
- A [Supabase](https://supabase.com) account (free tier works)

---

## 1. Create Supabase Project

1. Go to [supabase.com](https://supabase.com) and create a new project
2. Note your **Project URL**, **anon key**, and **JWT secret**:
   - Project URL: `Settings > API > Project URL`
   - Anon key: `Settings > API > Project API keys > anon public`
   - JWT secret: `Settings > API > JWT Settings > JWT Secret`
   - Database URL: `Settings > Database > Connection string > URI` (use "Transaction" mode)

3. Run the schema SQL:
   - Go to `SQL Editor` in the Supabase dashboard
   - Open and run the contents of `backend/supabase_schema.sql`
   - This creates the `profiles`, `api_keys`, and `usage_logs` tables with RLS policies

---

## 2. Configure Environment Variables

### Backend (`backend/.env`)

```env
OPENAI_API_KEY=sk-your-openai-key
DATABASE_URL=postgresql://postgres.[ref]:[password]@aws-0-[region].pooler.supabase.com:6543/postgres
SUPABASE_URL=https://[ref].supabase.co
SUPABASE_JWT_SECRET=your-jwt-secret
PORT=8000
```

### Frontend (`frontend/.env`)

```env
VITE_SUPABASE_URL=https://[ref].supabase.co
VITE_SUPABASE_ANON_KEY=your-anon-key
VITE_BACKEND_URL=http://localhost:8000
```

---

## 3. Run Locally

### Backend

```bash
cd backend
pip install -r requirements.txt
python semantic_cache_server.py
```

The backend starts at `http://localhost:8000`.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

The frontend starts at `http://localhost:3000`.

---

## 4. Deploy

### Frontend → Vercel

1. Push code to GitHub
2. Import the repo in [Vercel](https://vercel.com)
3. Set root directory to `frontend/`
4. Add environment variables:
   - `VITE_SUPABASE_URL`
   - `VITE_SUPABASE_ANON_KEY`
   - `VITE_BACKEND_URL` (your deployed backend URL)
5. Deploy — Vercel auto-detects Vite

### Backend → Railway (or Render)

1. Import the repo in [Railway](https://railway.app) or [Render](https://render.com)
2. Set root directory to `backend/`
3. Add environment variables:
   - `DATABASE_URL`
   - `SUPABASE_URL`
   - `SUPABASE_JWT_SECRET`
   - `OPENAI_API_KEY`
   - `ENCRYPTION_KEY` (generate with: `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`)
   - `PORT` (Railway sets this automatically)
4. Start command: `uvicorn semantic_cache_server:app --host 0.0.0.0 --port $PORT`

Both platforms provide automatic HTTPS.

---

## 5. Create an Admin User

After deploying, sign up normally via the frontend. Then in the Supabase dashboard:

1. Go to `Table Editor > profiles`
2. Find your user row
3. Set `is_admin` to `true`
4. Save

You can now access `/admin` in the frontend.
