# MotoExpert AI 🏍️

FastAPI application for motorcycle price analysis and depreciation tracking in Brazil.

## Features

- 🔍 **Consultar Desvalorização**: Analyze motorcycle depreciation by brand and model
- 🏆 **Relatórios VIP**: Exclusive reports for premium members (best buys, worst depreciations)
- ⚔️ **Tira-Teima**: Compare two motorcycles side-by-side
- 🔐 **VIP System**: Password-protected premium features via Google Sheets validation

## Local Development

### Install dependencies

```bash
uv sync
```

### Run the server

```bash
uv run uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Or use the shortcut:

```bash
uv run start
```

Open [http://localhost:8000](http://localhost:8000) in your browser.

## Deployment to Cloudflare

### Option 1: Cloudflare Pages with Functions

1. Push your code to GitHub
2. Connect your repository to Cloudflare Pages
3. Configure build settings:
   - **Framework preset**: None
   - **Build command**: `echo "No build needed"`
   - **Output directory**: `templates`

### Option 2: Cloudflare Workers with Python (Beta)

```bash
# Install Wrangler CLI
npm install -g wrangler

# Login to Cloudflare
wrangler login

# Deploy
wrangler deploy
```

## Project Structure

```
├── main.py                 # FastAPI application
├── auth_vip.py            # VIP authentication via Google Sheets
├── templates/
│   └── index.html         # Main HTML template with Alpine.js
├── static/                # Static files (CSS, JS, images)
├── base_motos_VIP_mestre.csv  # Motorcycle database
└── pyproject.toml        # Project dependencies
```

## API Endpoints

- `GET /` - Home page
- `POST /api/login` - VIP login
- `POST /api/analyze` - Analyze motorcycle depreciation
- `GET /api/vip/reports` - Get VIP reports
- `POST /api/compare` - Compare two motorcycles
- `GET /api/modelos/{marca}` - Get models by brand

## Tech Stack

- **Backend**: FastAPI, Uvicorn
- **Frontend**: Alpine.js, TailwindCSS, Plotly.js
- **Data**: Pandas
- **Authentication**: Google Sheets VIP codes

## License

MIT
