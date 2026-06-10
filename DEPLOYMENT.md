# Ujima SACCO - Deployment Guide

Complete guide for deploying the Ujima SACCO Multi-Agent microfinance platform.

## 📋 Table of Contents

1. [Local Development Setup](#local-development-setup)
2. [Project Structure](#project-structure)
3. [Deployment on Render](#deployment-on-render)
4. [Deployment on Heroku](#deployment-on-heroku)
5. [Docker Deployment](#docker-deployment)
6. [Environment Variables](#environment-variables)
7. [Production Checklist](#production-checklist)

---

## Local Development Setup

### Prerequisites
- Python 3.8+
- pip (Python package manager)
- Git

### Step 1: Clone or Download the Project

```bash
cd your-projects-directory
git clone https://github.com/yourusername/ujima-sacco.git
cd ujima-sacco
```

### Step 2: Create Virtual Environment

```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# macOS/Linux
python3 -m venv .venv
source .venv/bin/activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Configure Environment

Copy `.env.example` to `.env` and update values:

```bash
cp .env.example .env
```

Edit `.env` with your settings:

```env
APP_ENV=development
DEBUG=True
HOST=0.0.0.0
PORT=8000
RELOAD=True
```

### Step 5: Run the Application

```bash
# Option 1: Using the run script
python run.py

# Option 2: Direct uvicorn
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Visit: `http://127.0.0.1:8000`

---

## Project Structure

```
ujima-sacco/
├── app/                          # Backend application
│   ├── __init__.py
│   ├── main.py                   # FastAPI application
│   ├── models.py                 # Pydantic models
│   ├── db.py                     # Database/mock storage
│   ├── agents.py                 # Multi-agent orchestration
│   ├── compliance.py             # Compliance & security
│   └── __pycache__/
├── static/                       # Frontend (HTML, CSS, JS)
│   ├── index.html                # Home page
│   ├── app.html                  # Application form
│   ├── dashboard.html            # Member dashboard
│   ├── admin-dashboard.html      # Admin panel
│   ├── styles.css                # Styling
│   ├── app.js                    # Frontend JavaScript
│   └── README.md                 # Frontend docs
├── tests/                        # Unit tests
│   └── test_red_team.py
├── frontend/                     # Legacy frontend (kept for reference)
├── .env                          # Environment variables (local)
├── .env.example                  # Environment template
├── .gitignore                    # Git ignore rules
├── requirements.txt              # Python dependencies
├── Procfile                      # Deployment configuration
├── run.py                        # Application entry point
├── README.md                     # Project documentation
└── DEPLOYMENT.md                 # This file
```

---

## Deployment on Render

### Step 1: Prepare Your Repository

1. Push your code to GitHub:

```bash
git add .
git commit -m "Ready for deployment"
git push origin main
```

2. Ensure these files are in your repo:
   - `run.py` (entry point)
   - `requirements.txt` (dependencies)
   - `.env.example` (template, not `.env`)
   - `Procfile` (deployment config)

### Step 2: Create Render Account

1. Go to [render.com](https://render.com)
2. Sign up with GitHub
3. Click "New +" → "Web Service"
4. Select your GitHub repository
5. Configure:

| Setting | Value |
|---------|-------|
| **Name** | ujima-sacco |
| **Environment** | Python 3 |
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `python run.py` |
| **Plan** | Free/Paid (your choice) |

### Step 3: Add Environment Variables

In Render dashboard:

1. Go to "Environment" tab
2. Add variables from `.env.example`:

```
APP_ENV=production
DEBUG=False
HOST=0.0.0.0
PORT=8000
RELOAD=False
STORAGE_REGION=af-south-1
COMPLIANCE_MODE=mock
```

### Step 4: Deploy

Click "Create Web Service" and wait for deployment to complete.

Your app will be available at: `https://ujima-sacco-xxxx.onrender.com`

---

## Deployment on Heroku

### Step 1: Install Heroku CLI

Download from [heroku.com/download](https://www.heroku.com/download)

```bash
heroku login
```

### Step 2: Create Heroku App

```bash
heroku create ujima-sacco
```

### Step 3: Add Environment Variables

```bash
heroku config:set APP_ENV=production
heroku config:set DEBUG=False
heroku config:set RELOAD=False
```

### Step 4: Deploy

```bash
git push heroku main
```

View logs:

```bash
heroku logs --tail
```

Your app will be available at: `https://ujima-sacco.herokuapp.com`

---

## Docker Deployment

### Step 1: Create Dockerfile

Create `Dockerfile` in root directory:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health').read()"

# Run application
CMD ["python", "run.py"]
```

### Step 2: Create docker-compose.yml

```yaml
version: '3.8'

services:
  ujima-sacco:
    build: .
    ports:
      - "8000:8000"
    environment:
      - APP_ENV=production
      - DEBUG=False
      - RELOAD=False
    volumes:
      - .:/app
```

### Step 3: Build and Run

```bash
# Build image
docker build -t ujima-sacco .

# Run container
docker run -p 8000:8000 ujima-sacco

# Or use docker-compose
docker-compose up
```

---

## Environment Variables

### Configuration Variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `APP_ENV` | development | Environment mode (development/production) |
| `DEBUG` | True | Enable debug mode |
| `HOST` | 0.0.0.0 | Server host address |
| `PORT` | 8000 | Server port |
| `RELOAD` | False | Auto-reload on code changes |
| `LOG_LEVEL` | INFO | Logging level |
| `STORAGE_REGION` | af-south-1 | AWS region for storage |
| `COMPLIANCE_MODE` | mock | Compliance level (mock/strict) |

### Creating .env File

```bash
# Copy template
cp .env.example .env

# Edit .env with your values
# Never commit .env to version control
```

---

## Production Checklist

Before deploying to production:

- [ ] Set `APP_ENV=production`
- [ ] Set `DEBUG=False`
- [ ] Set `RELOAD=False`
- [ ] Update `CORS_ORIGINS` to specific domains
- [ ] Use environment variables for all secrets
- [ ] Test all API endpoints
- [ ] Verify database connectivity
- [ ] Enable logging to file
- [ ] Set up monitoring/alerts
- [ ] Configure backup strategy
- [ ] Review security headers
- [ ] Test SSL/TLS certificates
- [ ] Set up CI/CD pipeline
- [ ] Document API endpoints
- [ ] Create runbooks for incident response

### Security Checklist

- [ ] Disable debug mode
- [ ] Use strong secret keys
- [ ] Validate all inputs
- [ ] Implement rate limiting
- [ ] Use HTTPS only
- [ ] Set appropriate CORS headers
- [ ] Store secrets in environment variables
- [ ] Log security events
- [ ] Regular dependency updates
- [ ] Security audit of code

---

## Troubleshooting

### Common Issues

#### 1. Port Already in Use

```bash
# Find and kill process on port 8000
lsof -ti:8000 | xargs kill -9  # macOS/Linux
netstat -ano | findstr :8000   # Windows
```

#### 2. Module Not Found

```bash
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

#### 3. Static Files Not Loading

Ensure `static/` folder exists with frontend files.

#### 4. CORS Errors

Check CORS configuration in `app/main.py` and `.env`.

#### 5. Deployment Fails

- Check logs: `heroku logs --tail` or Render dashboard
- Verify `requirements.txt` is up to date
- Ensure `run.py` and `Procfile` are correct

---

## Monitoring & Maintenance

### Health Check

```bash
curl https://your-domain.com/health
```

Expected response:
```json
{
  "status": "healthy",
  "service": "Ujima SACCO",
  "environment": "production"
}
```

### Logs

View application logs:

```bash
# Render
render.com dashboard → Logs

# Heroku
heroku logs --tail

# Docker
docker logs ujima-sacco
```

### Performance Monitoring

Monitor key metrics:
- Response time
- Error rate
- Memory usage
- CPU usage
- Request count

---

## CI/CD Pipeline

Example GitHub Actions workflow (`.github/workflows/deploy.yml`):

```yaml
name: Deploy to Render

on:
  push:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Deploy to Render
        run: |
          curl -X POST ${{ secrets.RENDER_DEPLOY_HOOK }}
```

---

## Support & Documentation

- **API Documentation**: `/api/docs` (Swagger UI)
- **ReDoc**: `/api/redoc`
- **OpenAPI JSON**: `/api/openapi.json`
- **GitHub Issues**: Report bugs and request features
- **Email**: support@ujima-sacco.com

---

## License

Ujima SACCO © 2026. All rights reserved.
Kenya Data Protection Act 2022 Compliant.

