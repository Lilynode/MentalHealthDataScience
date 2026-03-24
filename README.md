# Mental Health Risk Assessment System (MHRAS)

A comprehensive mental health screening system with ML-powered risk assessment, clinical decision support, and resource recommendations.

## Quick Start

### Deploy to Vercel (Frontend + Serverless API)

```bash
npm install -g vercel
vercel
```

**Demo Mode**: Deploys with simulated ML predictions (no backend required)
**Full Stack**: Set `MHRAS_API_URL` environment variable to connect to FastAPI backend

### Deploy Full Stack

1. **Backend**: Deploy FastAPI to Railway/Render/etc. with PostgreSQL + Redis
2. **Frontend**: Deploy to Vercel with `MHRAS_API_URL` env var pointing to your backend

## Features

- **Mental Health Screening** - PHQ-9, GAD-7, wearable data, EMR integration
- **ML Risk Assessment** - Ensemble models (Logistic Regression, LightGBM)
- **Interpretable Predictions** - SHAP values, counterfactuals, clinical explanations
- **Resource Recommendations** - Crisis lines, therapy, support groups, medication resources
- **Governance & Compliance** - Consent verification, audit logging, human review queue
- **Batch Processing** - Screen up to 100 individuals at once

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/health` | GET | Health check |
| `/api/screen` | POST | Single screening request |
| `/api/batch-screen` | POST | Batch screening (max 100) |

## Configuration

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `MHRAS_API_URL` | No | Full URL to FastAPI backend (enables full-stack mode) |

### Vercel Configuration

See `vercel.json` for build settings, function timeouts, and headers.

## Local Development

```bash
# Frontend only (static)
python -m http.server 3000

# Full stack (requires PostgreSQL + Redis)
docker-compose up
```

## Architecture

```
Vercel (Frontend + Serverless)
├── index.html, app.js, styles.css (Static)
└── api/
    ├── health.js
    ├── screen.js
    └── batch-screen.js
         │
         ▼ (optional proxy)
    FastAPI Backend (Railway/Render)
    ├── ML Models
    ├── PostgreSQL
    └── Redis
```

## Deployment Documentation

See `VERCEL_DEPLOY.md` for detailed deployment instructions.

## License

Proprietary - For authorized clinical use only.
