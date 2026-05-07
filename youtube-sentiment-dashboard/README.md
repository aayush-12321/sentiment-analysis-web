# 🎯 SentimentScope — YouTube Brand Sentiment Dashboard

A production-ready Brand24-style dashboard that analyses YouTube comment sentiment for any brand or keyword in real time.

**Stack:** Flask + VADER · React + Recharts · PostgreSQL · Docker · Gunicorn + Nginx

---

## ✨ Features

| Feature | Details |
|---|---|
| **Sentiment Analysis** | VADER (offline, zero API cost, emoji-aware) |
| **Charts** | Donut pie · Stacked area trend · Animated score gauge |
| **Comment Table** | Sortable by likes / score / date · Paginated · Filtered by sentiment |
| **Caching** | In-memory (Flask-Cache) + PostgreSQL persistent cache |
| **Search History** | Recent keyword audit log stored in PostgreSQL |
| **Deployment** | Docker Compose · Gunicorn · Nginx with rate limiting |

---

## 🗂 Project Structure

```
youtube-sentiment-dashboard/
├── backend/
│   ├── app.py                  # Flask factory
│   ├── wsgi.py                 # Gunicorn entry point
│   ├── gunicorn.conf.py        # Gunicorn settings
│   ├── models.py               # SQLAlchemy models (PostgreSQL)
│   ├── requirements.txt
│   ├── .env.example            # ← copy to .env
│   ├── routes/
│   │   ├── sentiment.py        # /api/analyze-brand, /api/top-comments, /api/history
│   │   └── health.py           # /api/health
│   ├── services/
│   │   ├── youtube_service.py  # YouTube Data API v3
│   │   ├── sentiment_service.py# VADER analysis + aggregation
│   │   └── cache_service.py    # Memory + PostgreSQL cache layer
│   └── utils/
│       └── validators.py       # Input sanitisation
│
├── frontend/
│   ├── index.html
│   ├── vite.config.js
│   ├── package.json
│   └── src/
│       ├── App.jsx / App.module.css
│       ├── main.jsx
│       ├── hooks/useSentiment.js
│       ├── utils/api.js
│       ├── styles/global.css
│       └── components/
│           ├── SearchBar.jsx
│           ├── StatCards.jsx
│           ├── CommentTable.jsx
│           ├── ScoreGauge.jsx
│           ├── charts/
│           │   ├── SentimentPieChart.jsx
│           │   └── SentimentTrend.jsx
│           └── ui/
│               ├── LoadingState.jsx
│               ├── ErrorBanner.jsx
│               └── EmptyState.jsx
│
├── nginx/nginx.conf            # Standalone Nginx config
├── docker/
│   ├── Dockerfile.backend
│   ├── Dockerfile.frontend
│   └── nginx.frontend.conf
├── docker-compose.yml
└── .gitignore
```

---

## 🚀 Quick Start — Local Development

### 1. Get a YouTube Data API v3 Key

1. Go to [Google Cloud Console](https://console.developers.google.com/)
2. Create a project → **Enable** "YouTube Data API v3"
3. Create credentials → **API Key**

### 2. Backend setup

```bash
cd backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate           # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env — set YOUTUBE_API_KEY and DATABASE_URL

# Start PostgreSQL (or use SQLite by removing DATABASE_URL for dev)
# Then run:
flask --app wsgi:application run --port 5000
```

### 3. Frontend setup

```bash
cd frontend
npm install
npm run dev           # Starts on http://localhost:3000
```

Vite proxies `/api/*` → `localhost:5000` automatically.

---

## 🐳 Docker Compose (Recommended for Production)

```bash
# 1. Configure secrets
cp backend/.env.example backend/.env
# Fill in: YOUTUBE_API_KEY, FLASK_SECRET_KEY

# 2. Build and start all services
docker compose up --build -d

# 3. Check logs
docker compose logs -f

# 4. Open in browser
open http://localhost
```

Services started:
- `db`        → PostgreSQL 16 on internal network
- `backend`   → Flask/Gunicorn on port 5000
- `frontend`  → React/Nginx on port 80

---

## 🖥 Manual Production Deployment (VPS)

### Step 1 — Build the React app

```bash
cd frontend
npm install
npm run build
# Output: frontend/dist/
```

### Step 2 — Copy static files to Nginx web root

```bash
sudo mkdir -p /var/www/sentimentscope
sudo cp -r frontend/dist/* /var/www/sentimentscope/
```

### Step 3 — Configure Nginx

```bash
sudo cp nginx/nginx.conf /etc/nginx/nginx.conf
sudo nginx -t && sudo systemctl restart nginx
```

### Step 4 — Run Gunicorn

```bash
cd backend
pip install -r requirements.txt
gunicorn -c gunicorn.conf.py wsgi:application
```

Or use **systemd** for process management:

```ini
# /etc/systemd/system/sentimentscope.service
[Unit]
Description=SentimentScope Flask API
After=network.target postgresql.service

[Service]
User=www-data
WorkingDirectory=/opt/sentimentscope/backend
EnvironmentFile=/opt/sentimentscope/backend/.env
ExecStart=/opt/sentimentscope/venv/bin/gunicorn -c gunicorn.conf.py wsgi:application
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable --now sentimentscope
```

---

## 📡 API Reference

### `GET /api/analyze-brand`

Fetch and analyse YouTube comments for a keyword.

| Param | Type | Default | Description |
|---|---|---|---|
| `keyword` | string | required | Brand name or search term |
| `max_videos` | int | 5 | Number of videos to scan (1–20) |
| `max_comments` | int | 20 | Comments per video (1–100) |

**Response 200:**
```json
{
  "keyword": "Nike",
  "cached": false,
  "summary": {
    "total": 87,
    "positive": 52,
    "negative": 18,
    "neutral": 17,
    "avg_score": 0.1823,
    "positivePercent": 59.8,
    "negativePercent": 20.7,
    "neutralPercent": 19.5,
    "mostPositiveComment": { ... },
    "mostNegativeComment": { ... }
  },
  "trend": [
    { "date": "2024-11-01", "positive": 8, "negative": 3, "neutral": 2 }
  ],
  "topByLabel": {
    "positive": [ ... ],
    "negative": [ ... ],
    "neutral":  [ ... ]
  },
  "comments": [ ... ]
}
```

**Error codes:** `400` invalid keyword · `403` quota/key issue · `404` no comments · `502` YouTube error

---

### `GET /api/top-comments`

| Param | Type | Default | Description |
|---|---|---|---|
| `keyword` | string | required | Must match a cached analysis |
| `sentiment` | string | `all` | `positive` / `negative` / `neutral` / `all` |
| `limit` | int | 10 | Max comments returned (1–50) |

---

### `GET /api/history`

Returns the 20 most recently searched unique keywords.

---

### `GET /api/health`

```json
{ "status": "ok", "database": "connected", "youtube_key_present": true }
```

---

## ⚙️ Configuration Reference (`.env`)

| Variable | Required | Description |
|---|---|---|
| `YOUTUBE_API_KEY` | ✅ | YouTube Data API v3 key |
| `FLASK_SECRET_KEY` | ✅ | Strong random string for Flask sessions |
| `DATABASE_URL` | ✅ | PostgreSQL connection string |
| `FLASK_ENV` | — | `development` or `production` |
| `CACHE_TIMEOUT` | — | Cache TTL in seconds (default: 600) |
| `MAX_VIDEOS` | — | Default videos per search (default: 5) |
| `MAX_COMMENTS_PER_VIDEO` | — | Default comments per video (default: 20) |
| `CORS_ORIGINS` | — | Comma-separated allowed origins |

---

## 🔍 Sentiment Analysis

VADER classifies each comment with a compound score from **−1.0** (most negative) to **+1.0** (most positive).

| Score | Label |
|---|---|
| ≥ +0.05 | Positive |
| ≤ −0.05 | Negative |
| Between | Neutral |

VADER is purpose-built for social media text — it handles emoji, slang, ALL-CAPS emphasis, and punctuation chains without any external API calls.

---

## 🛡 Production Notes

- **API quota:** YouTube Data API v3 has a default quota of 10,000 units/day. Each search costs ~100 units. Caching (10 min default) dramatically reduces repeat usage.
- **Scaling:** Swap `SimpleCache` for `RedisCache` in `app.py` when running multiple Gunicorn workers.
- **HTTPS:** Add Certbot/Let's Encrypt to the Nginx config for TLS.
- **Secrets:** Never commit `.env`. Use Docker secrets or a secrets manager in production.
