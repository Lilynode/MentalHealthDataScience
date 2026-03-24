# Vercel Deployment

This project can be deployed to Vercel with two modes:

## Mode 1: Demo Mode (No Backend Required)

Deploy the frontend with serverless API functions that return simulated responses:

```bash
npm install -g vercel
vercel
```

This will deploy:
- `index.html`, `app.js`, `styles.css` → Static site
- `api/` → Serverless functions (return simulated ML predictions)

## Mode 2: Full Stack (With Backend)

Set the `MHRAS_API_URL` environment variable to point to your FastAPI backend:

```bash
vercel env add MHRAS_API_URL
# Set to: https://your-backend.railway.app (or your deployed backend URL)
vercel
```

The serverless functions will proxy requests to your FastAPI backend.

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `MHRAS_API_URL` | No | Full URL to FastAPI backend (e.g., `https://mhras-api.railway.app`) |

## Deploy Buttons

### Railway (Backend + PostgreSQL + Redis)
[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app)

1. Deploy FastAPI backend to Railway with PostgreSQL and Redis
2. Note the backend URL
3. Deploy frontend to Vercel with `MHRAS_API_URL` set

### Vercel (Frontend)
[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com)

## Local Development

```bash
# Terminal 1: Run FastAPI backend
python -m src.cli serve

# Terminal 2: Run Vercel dev server for frontend
cd frontend && python -m http.server 3000
# Or: npx serve .
```

## API Endpoints (Serverless)

When deployed to Vercel, the following endpoints are available:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/health` | GET | Health check |
| `/api/screen` | POST | Single screening request |
| `/api/batch-screen` | POST | Batch screening (max 100) |

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Vercel                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │   Frontend   │  │  /api/health │  │ /api/screen  │       │
│  │   (Static)   │  │  (Serverless)│  │ (Serverless)│       │
│  └──────────────┘  └──────────────┘  └──────────────┘       │
│         │                                      │            │
│         └────────────── proxy ──────────────────┘            │
│                            │                               │
│                     (if MHRAS_API_URL                       │
│                      is configured)                         │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼ (optional)
┌─────────────────────────────────────────────────────────────┐
│                      Railway                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │   FastAPI    │  │  PostgreSQL  │  │    Redis     │     │
│  │   Backend   │  │   Database   │  │    Cache     │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└─────────────────────────────────────────────────────────────┘
```
