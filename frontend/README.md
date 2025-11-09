# Semantis AI Frontend Dashboard

A premium, developer-first dashboard for monitoring and managing semantic cache performance for LLM APIs.

## Features

- **Query Playground**: Test LLM queries and see cache hits in real-time
- **Performance Metrics**: Monitor hit ratios, latency, and cost savings
- **Event Logs**: View detailed cache decision logs
- **Settings**: Adjust similarity threshold and TTL
- **Documentation**: Copy-paste integration examples for Python and Node.js

## Getting Started

### Prerequisites

- Node.js 18+
- Backend running at `http://localhost:8000`

### Installation

```bash
npm install
```

### Environment Variables

Create a `.env` file:

```
VITE_BACKEND_URL=http://localhost:8000
```

### Development

```bash
npm run dev
```

The app will be available at `http://localhost:3000`

### Build

```bash
npm run build
```

## Architecture

```
src/
├── api/           # Backend API wrappers
├── components/    # Reusable UI components
├── hooks/         # Custom React hooks
├── pages/         # Page components
└── App.tsx        # Main application
```

## Authentication

The frontend uses API key authentication stored in localStorage. No signup/login flows are required.

## API Integration

All API calls use the `Authorization: Bearer` header with the format `sc-{tenant}-{uuid}`.

## Design

The UI follows a dark, futuristic theme inspired by Vercel and Arc, with:

- Glassmorphism effects
- Animated backgrounds (Prism & LightRays)
- Smooth transitions
- Clear visual hierarchy
- High contrast for readability

## License

ISC
