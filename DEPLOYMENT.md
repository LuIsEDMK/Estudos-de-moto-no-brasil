# Deployment Guide 🚀

## Option 1: Cloudflare Pages (Recommended for Static + API)

Cloudflare Pages doesn't natively support Python backends, but you have options:

### A. Use Cloudflare Pages with External API
1. Deploy frontend to Cloudflare Pages
2. Deploy FastAPI backend to another platform (Railway, Render, Fly.io)
3. Connect them via API calls

### B. Use Cloudflare Workers with Python (Beta)
Python Workers is in beta. Check availability in your account.

```bash
# Install Wrangler
npm install -g wrangler

# Login
wrangler login

# Deploy
wrangler deploy
```

## Option 2: Railway.app (Easiest for FastAPI)

1. Push code to GitHub
2. Go to [railway.app](https://railway.app)
3. Click "New Project" → "Deploy from GitHub"
4. Select your repository
5. Railway auto-detects `pyproject.toml` and deploys

**Environment Variables:**
- Set any required env vars in Railway dashboard

## Option 3: Render.com (Free Tier)

1. Push to GitHub
2. Go to [render.com](https://render.com)
3. Create "Web Service"
4. Connect repository
5. Configure:
   - **Build Command**: `pip install -e .`
   - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`

## Option 4: Fly.io

```bash
# Install Fly CLI
curl -L https://fly.io/install.sh | sh

# Login
fly auth login

# Initialize
fly launch --name motoexpert-ai

# Deploy
fly deploy
```

## Option 5: Hugging Face Spaces (Free!)

1. Create a new Space at [huggingface.co/spaces](https://huggingface.co/spaces)
2. Choose "Docker" as SDK
3. Create `Dockerfile`:

```dockerfile
FROM python:3.12-slim

WORKDIR /app

RUN pip install uv
COPY . .
RUN uv sync --frozen

CMD ["uv", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "7860"]
```

4. Push to the Space repository

## Option 6: Vercel (with Python Serverless Functions)

Vercel supports Python serverless functions:

1. Restructure project:
```
├── api/
│   └── index.py  # Move FastAPI routes here
├── templates/
└── vercel.json
```

2. Create `vercel.json`:
```json
{
  "version": 2,
  "builds": [
    {
      "src": "api/index.py",
      "use": "@vercel/python"
    }
  ],
  "routes": [
    {
      "src": "/(.*)",
      "dest": "api/index.py"
    }
  ]
}
```

3. Deploy:
```bash
npm install -g vercel
vercel
```

## Quick Test Locally

```bash
# Run with uv
uv run uvicorn main:app --reload

# Or use the shortcut
uv run start
```

Then open http://localhost:8000

## Important Notes

### For Cloudflare Specifically:
Cloudflare's infrastructure is optimized for:
- Static sites (Pages)
- JavaScript/TypeScript Workers
- Edge functions

For Python FastAPI apps, consider:
1. **Railway** - Best DX, auto-deploys from GitHub
2. **Render** - Free tier available
3. **Fly.io** - Global deployment, $5 credit free
4. **Hugging Face Spaces** - Completely free for public apps

### Environment Variables
Set these in your deployment platform:
- Any API keys
- Google Sheets URL (if different)
- Session secrets

### Database Considerations
Currently using in-memory sessions. For production:
- Use Redis for sessions
- Add proper database (PostgreSQL, MongoDB)
- Implement caching for CSV data
