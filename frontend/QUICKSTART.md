# Quick Start Guide

## Prerequisites

1. Backend API running at `http://localhost:8000`
2. Node.js 18+ installed
3. API key with format `sc-{tenant}-{any}` (e.g., `sc-demo-abc123`)

## Installation & Setup

```bash
cd frontend
npm install
```

## Running the Development Server

```bash
npm run dev
```

The frontend will be available at `http://localhost:3000`

## Using the Dashboard

### Step 1: Enter Your API Key

On the landing page, paste your Semantis API key. It will be stored securely in localStorage.

### Step 2: Test Queries in Playground

Navigate to the Playground page and:
- Enter a prompt (e.g., "Explain semantic caching")
- Select a model (gpt-4o-mini, gpt-4, etc.)
- Adjust temperature if needed
- Click "Run Query"

You'll see:
- Cache hit type (exact/semantic/miss)
- Similarity score
- Response latency
- The LLM response

### Step 3: Monitor Metrics

Visit the Metrics page to see:
- Hit ratio (overall & semantic)
- Average latency
- Total requests
- Tokens saved estimate

### Step 4: View Logs

The Logs page shows all recent cache decisions with:
- Timestamp
- Decision type
- Similarity score
- Latency
- Prompt hash

You can download logs as CSV for further analysis.

### Step 5: Adjust Settings

In Settings, you can configure:
- Similarity threshold (0.5 - 1.0)
- Default TTL (1-90 days)

Note: Some settings require backend support to take effect.

### Step 6: Integration

Visit the Docs page for copy-paste examples:
- Python SDK
- Node.js SDK
- cURL examples

All code snippets include your API key (masked) for easy integration.

## Backend Integration

The frontend expects these endpoints:

- `GET /health` - Health check
- `GET /metrics` - Performance metrics (requires auth)
- `GET /events?limit=N` - Recent events (requires auth)
- `POST /v1/chat/completions` - OpenAI-compatible endpoint (requires auth)

All authenticated requests must include:
```
Authorization: Bearer sc-{tenant}-{uuid}
```

## Environment Variables

Create a `.env` file:
```
VITE_BACKEND_URL=http://localhost:8000
```

## Building for Production

```bash
npm run build
```

The built files will be in the `dist/` directory.

## Troubleshooting

### Backend Connection Issues

Check the health indicator in the top nav bar:
- Green dot = Connected
- Yellow dot = Checking
- Red dot = Disconnected

Make sure the backend is running at the configured URL.

### API Key Issues

API keys must:
- Start with `sc-`
- Be in format `sc-{tenant}-{uuid}`
- Have valid authentication on the backend

### CORS Errors

If you see CORS errors, ensure the backend allows requests from `http://localhost:3000`.

## Architecture

```
/                  → Landing page with API key input
/playground        → Query testing interface
/metrics           → Performance dashboard
/logs              → Event logs viewer
/settings          → Cache configuration
/docs              → Integration documentation
```

All routes except `/` require authentication (API key in localStorage).

## Features

- **No login required** - Just paste your API key
- **Real-time updates** - Metrics refresh automatically
- **Dark mode only** - Premium, futuristic design
- **Animated backgrounds** - Prism & LightRays effects
- **Responsive design** - Works on all screen sizes
- **Copy-paste ready** - Integration examples with your key

## Support

For backend setup and API documentation, see the main project README.
