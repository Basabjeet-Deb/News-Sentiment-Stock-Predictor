# MarketBrief Setup Guide

Complete installation and configuration guide for the MarketBrief AI Stock Analysis Platform.

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Installation](#installation)
3. [Environment Configuration](#environment-configuration)
4. [LM Studio Setup (AI Chatbot)](#lm-studio-setup-ai-chatbot)
5. [Running the Application](#running-the-application)
6. [Data Collection](#data-collection)
7. [Model Training](#model-training)
8. [Troubleshooting](#troubleshooting)
9. [Advanced Configuration](#advanced-configuration)

---

## Prerequisites

### System Requirements

- **Operating System**: Windows 10/11, macOS 10.15+, or Linux (Ubuntu 20.04+)
- **Python**: 3.9 or higher
- **RAM**: Minimum 8GB (16GB recommended for model training)
- **Storage**: 5GB free space for data and models
- **Internet**: Required for news scraping and price data

### Required Software

1. **Python 3.9+**
   - Download from [python.org](https://www.python.org/downloads/)
   - Verify installation: `python --version`

2. **pip** (Python package manager)
   - Usually included with Python
   - Verify: `pip --version`

3. **Git** (optional, for cloning repository)
   - Download from [git-scm.com](https://git-scm.com/)

---

## Installation

### Step 1: Clone or Download Repository

**Option A: Using Git**
```bash
git clone https://github.com/Basabjeet-Deb/News-Sentiment-Stock-Predictor.git
cd News-Sentiment-Stock-Predictor
```

**Option B: Download ZIP**
1. Visit [GitHub Repository](https://github.com/Basabjeet-Deb/News-Sentiment-Stock-Predictor)
2. Click "Code" → "Download ZIP"
3. Extract and navigate to folder

### Step 2: Create Virtual Environment (Recommended)

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

This will install:
- **FastAPI** - Web framework
- **Uvicorn** - ASGI server
- **Scrapy** - Web scraping
- **Pandas** - Data manipulation
- **NumPy** - Numerical computing
- **scikit-learn** - Machine learning
- **LightGBM** - Gradient boosting
- **XGBoost** - Gradient boosting
- **yfinance** - Stock price data
- **VADER Sentiment** - Sentiment analysis
- **Optuna** - Hyperparameter tuning
- **Requests** - HTTP library
- **python-dotenv** - Environment variables

### Step 4: Verify Installation

```bash
python -c "import fastapi, pandas, sklearn, lightgbm, xgboost; print('All packages installed successfully!')"
```

---

## Environment Configuration

### Step 1: Create Environment File

Copy the example environment file:

```bash
# Windows
copy .env.example .env

# macOS/Linux
cp .env.example .env
```

### Step 2: Configure Environment Variables

Open `.env` in a text editor and configure the following:

#### Required Settings

```env
# Application Settings
APP_NAME=MarketBrief
APP_VERSION=1.0.0
DEBUG=False

# Server Configuration
HOST=0.0.0.0
PORT=8000

# CORS Settings (for frontend)
CORS_ORIGINS=http://localhost:8000,http://127.0.0.1:8000
```

#### LM Studio Configuration (Optional - for AI Chatbot)

```env
# LM Studio API Configuration
LM_STUDIO_URL=http://127.0.0.1:1234/v1/chat/completions
LM_STUDIO_MODEL=google/gemma-4-e4b
LM_STUDIO_API_TOKEN=your_token_here
LM_STUDIO_TIMEOUT=10.0
LM_STUDIO_MAX_TOKENS=45
LM_STUDIO_TEMPERATURE=0.2
LM_STUDIO_TOP_P=0.8
```

#### External API Keys (Optional)

```env
# Alpha Vantage (alternative price data source)
ALPHA_VANTAGE_API_KEY=your_key_here

# Financial Modeling Prep (alternative data source)
FMP_API_KEY=your_key_here
```

### Step 3: Security Best Practices

⚠️ **Important Security Notes:**

- **Never commit `.env` to version control** (already in `.gitignore`)
- Use strong, unique API tokens
- Rotate tokens regularly
- Use different `.env` files for development/production
- Keep `.env.example` updated without sensitive data

---

## LM Studio Setup (AI Chatbot)

The AI chatbot feature requires LM Studio for local LLM inference.

### Step 1: Install LM Studio

1. Download from [lmstudio.ai](https://lmstudio.ai/)
2. Install for your operating system
3. Launch LM Studio

### Step 2: Download a Model

**Recommended Model: `google/gemma-4-e4b`** (thinking model)

1. Open LM Studio
2. Go to "Discover" tab
3. Search for "google/gemma-4-e4b"
4. Click "Download"
5. Wait for download to complete

**Alternative Models:**
- `meta-llama/Llama-3.2-3B-Instruct`
- `microsoft/Phi-3-mini-4k-instruct`
- `mistralai/Mistral-7B-Instruct-v0.2`

### Step 3: Start Local Server

1. Go to "Local Server" tab in LM Studio
2. Select your downloaded model
3. Click "Start Server"
4. Default URL: `http://127.0.0.1:1234`
5. Note the port number (usually 1234)

### Step 4: Get API Token

1. In LM Studio, go to "Local Server" settings
2. Find or generate API token
3. Copy the token
4. Paste into `.env` file:
   ```env
   LM_STUDIO_API_TOKEN=sk-lm-your-token-here
   ```

### Step 5: Test Connection

```bash
python test_lm_studio.py
```

Expected output:
```
✓ LM Studio is running
✓ Model loaded: google/gemma-4-e4b
✓ Test query successful
```

### Troubleshooting LM Studio

**Issue: Connection refused**
- Ensure LM Studio server is running
- Check port number matches `.env` configuration
- Verify firewall isn't blocking localhost connections

**Issue: Slow responses**
- Reduce `LM_STUDIO_MAX_TOKENS` in `.env`
- Use a smaller model
- Ensure sufficient RAM available

**Issue: Model not loading**
- Check model is fully downloaded
- Restart LM Studio
- Try a different model

---

## Running the Application

### Method 1: Using Batch Script (Windows)

```bash
start_backend.bat
```

This script:
- Activates virtual environment (if exists)
- Loads environment variables
- Starts FastAPI server on port 8000

### Method 2: Manual Start

```bash
# Activate virtual environment first
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Method 3: Production Mode

```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Accessing the Application

Once started, open your browser:

- **Main Application**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Alternative API Docs**: http://localhost:8000/redoc

### Verify Application is Running

```bash
curl http://localhost:8000/api/v1/predictions/summary
```

Expected response:
```json
{
  "total": 528,
  "by_recommendation": {...},
  "by_sector": {...}
}
```

---

## Data Collection

### Initial Data Setup

The repository includes pre-collected data. To update or collect new data:

### Step 1: Collect Today's News

```bash
python collect_missing_dates.py --today
```

This will:
- Scrape news from 8 major sources
- Process ~500-1000 articles
- Save to `data/gdelt_cache/`
- Update `data/news_events.csv`

### Step 2: Collect Historical Data (Optional)

```bash
# Collect specific date
python collect_one_date.py 2026-04-28

# Collect date range
python collect_missing_dates.py --start 2026-04-01 --end 2026-04-28
```

### Step 3: Verify Data Collection

```bash
# Check news events
python -c "import pandas as pd; df = pd.read_csv('data/news_events.csv'); print(f'Total articles: {len(df)}')"

# Check latest date
python -c "import pandas as pd; df = pd.read_csv('data/news_events.csv'); print(f'Latest date: {df[\"date\"].max()}')"
```

### Data Collection Schedule

**Recommended Schedule:**
- **Daily**: Run `collect_missing_dates.py --today` after market close
- **Weekly**: Verify data quality and fill any gaps
- **Monthly**: Archive old cache files to save space

### Automated Daily Updates

**Windows Task Scheduler:**
1. Open Task Scheduler
2. Create Basic Task
3. Trigger: Daily at 5:00 PM (after market close)
4. Action: Start program
5. Program: `python`
6. Arguments: `collect_missing_dates.py --today --run-pipeline`
7. Start in: `C:\path\to\News-Sentiment-Stock-Predictor`

**Linux/macOS Cron:**
```bash
# Edit crontab
crontab -e

# Add daily job (5 PM)
0 17 * * * cd /path/to/News-Sentiment-Stock-Predictor && python collect_missing_dates.py --today --run-pipeline
```

---

## Model Training

### Step 1: Build Training Data

```bash
# Via API
curl -X POST http://localhost:8000/api/v1/training/collect-data

# Or via UI
# Navigate to "Training" tab → Click "Rebuild Training Data"
```

This creates:
- `data/daily_panel.csv` - Full dataset
- `data/daily_panel_balanced.csv` - Balanced dataset (recommended)

### Step 2: Train Model

```bash
# Via API
curl -X POST http://localhost:8000/api/v1/training/train-model

# Or via UI
# Navigate to "Training" tab → Click "Train Model"
```

Training process:
1. Loads balanced training data (~2,000 rows)
2. Runs Optuna hyperparameter tuning (30 trials)
3. Trains ensemble (LightGBM + XGBoost + RandomForest)
4. Saves model to `data/forecaster_model.pkl`
5. Saves metrics to `data/forecaster_meta.json`

### Step 3: Verify Model

```bash
# Check model file exists
ls -lh data/forecaster_model.pkl

# View model metrics
cat data/forecaster_meta.json
```

Expected metrics:
```json
{
  "accuracy": 0.49,
  "f1_score": 0.568,
  "auc": 0.496,
  "training_samples": 2012,
  "features": 23,
  "trained_at": "2026-04-28T10:30:00"
}
```

### Model Training Tips

**Improving Model Performance:**
1. Collect more historical data (increase training samples)
2. Adjust class weights in `pipeline/forecaster.py`
3. Increase Optuna trials (slower but better tuning)
4. Add more technical indicators
5. Experiment with different sentiment models

**Training Time:**
- Small dataset (2K rows): ~2-5 minutes
- Medium dataset (10K rows): ~10-20 minutes
- Large dataset (50K rows): ~30-60 minutes

---

## Troubleshooting

### Common Issues

#### 1. Port Already in Use

**Error:** `Address already in use`

**Solution:**
```bash
# Windows - Find and kill process
netstat -ano | findstr :8000
taskkill /PID <process_id> /F

# macOS/Linux
lsof -ti:8000 | xargs kill -9
```

#### 2. Module Not Found

**Error:** `ModuleNotFoundError: No module named 'fastapi'`

**Solution:**
```bash
# Ensure virtual environment is activated
# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

#### 3. Permission Denied

**Error:** `PermissionError: [Errno 13] Permission denied`

**Solution:**
```bash
# Windows - Run as Administrator
# macOS/Linux - Check file permissions
chmod +x start_backend.bat
chmod -R 755 data/
```

#### 4. LM Studio Connection Failed

**Error:** `Connection refused to LM Studio`

**Solution:**
1. Verify LM Studio is running
2. Check server is started in LM Studio
3. Verify port in `.env` matches LM Studio
4. Test connection: `curl http://127.0.0.1:1234/v1/models`

#### 5. Out of Memory

**Error:** `MemoryError` during training

**Solution:**
- Reduce training data size
- Use balanced dataset (smaller)
- Close other applications
- Increase system swap/page file
- Use smaller ML models

#### 6. Slow News Scraping

**Issue:** Scraping takes too long

**Solution:**
- Check internet connection
- Reduce concurrent requests in `pipeline/news_spider.py`
- Use cached data when available
- Skip problematic sources temporarily

---

## Advanced Configuration

### Custom Ticker List

Edit `config.py` to modify tracked tickers:

```python
TICKERS = [
    'AAPL', 'MSFT', 'GOOGL',  # Add your tickers
    # ... more tickers
]
```

### Adjust Model Parameters

Edit `pipeline/forecaster.py`:

```python
# Optuna trials (more = better tuning, slower)
N_TRIALS = 30  # Default: 30, increase to 50-100

# Ensemble weights
WEIGHTS = {
    'lgb': 1.2,    # LightGBM weight
    'xgb': 1.0,    # XGBoost weight
    'rf': 0.8      # RandomForest weight
}
```

### Custom News Sources

Edit `pipeline/news_spider.py` to add RSS feeds:

```python
start_urls = [
    'https://news.google.com/rss/search?q=stocks',
    'https://your-custom-source.com/rss',  # Add here
]
```

### Database Integration (Future)

To use PostgreSQL instead of CSV files:

1. Install psycopg2: `pip install psycopg2-binary`
2. Add to `.env`:
   ```env
   DATABASE_URL=postgresql://user:pass@localhost:5432/marketbrief
   ```
3. Modify data loading in `app/services/`

### API Rate Limiting

Adjust rate limits in `app/middleware/rate_limit.py`:

```python
# Requests per minute
RATE_LIMIT = 60  # Default: 60

# Burst allowance
BURST = 10  # Default: 10
```

### Logging Configuration

Edit `app/core/logging_config.py`:

```python
# Log level
LOG_LEVEL = "INFO"  # DEBUG, INFO, WARNING, ERROR

# Log file rotation
MAX_BYTES = 10485760  # 10MB
BACKUP_COUNT = 5  # Keep 5 old logs
```

---

## Production Deployment

### Using Docker (Recommended)

Create `Dockerfile`:

```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Build and run:
```bash
docker build -t marketbrief .
docker run -p 8000:8000 --env-file .env marketbrief
```

### Using Nginx Reverse Proxy

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### Using Systemd (Linux)

Create `/etc/systemd/system/marketbrief.service`:

```ini
[Unit]
Description=MarketBrief API
After=network.target

[Service]
Type=simple
User=your-user
WorkingDirectory=/path/to/News-Sentiment-Stock-Predictor
Environment="PATH=/path/to/venv/bin"
ExecStart=/path/to/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable marketbrief
sudo systemctl start marketbrief
```

---

## Support

### Getting Help

- **GitHub Issues**: [Report bugs or request features](https://github.com/Basabjeet-Deb/News-Sentiment-Stock-Predictor/issues)
- **Email**: basabjeet.557@gmail.com
- **Documentation**: [README.md](README.md)

### Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

---

## License

Proprietary Software — © 2026 Basabjeet Deb  
All rights reserved. See [LICENSE](LICENSE) for full terms.

---

## Changelog

### Version 1.0.0 (2026-04-28)
- Initial release
- AI chatbot with LM Studio integration
- Ensemble ML model (LightGBM + XGBoost + RandomForest)
- 268K+ news articles analyzed
- 541 stocks tracked
- Dark/light theme UI
- Real-time predictions

---

**Last Updated:** April 28, 2026  
**Author:** Basabjeet Deb  
**Repository:** https://github.com/Basabjeet-Deb/News-Sentiment-Stock-Predictor
