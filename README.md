# IR Search Engine & Document Classification System

> **ST7071CEM - Intelligent Information Retrieval Assignment**  
> **Author:** Shishir Kandel
> **Institution:** Coventry University / Softwarica College

## 🚀 Quick Start

### 1. Database Setup (Run once)
```powershell
# Create PostgreSQL database (run in psql)
psql -U postgres
CREATE DATABASE ir_search_engine;
CREATE USER ir_user WITH PASSWORD '#Sishir123';
GRANT ALL PRIVILEGES ON DATABASE ir_search_engine TO ir_user;
\q
```

### 2. Backend Setup
```powershell
cd backend

# Activate virtual environment
..\venv\Scripts\activate

# Run migrations
python manage.py migrate

# Import training data
python manage.py import_training_data --file ../data/training_documents.csv

# Train classification models
python manage.py train_models

# Start Django server
python manage.py runserver
```

### 2b. Scheduled Crawling (Celery + Redis)
Scheduled crawling requires a running Redis broker and Celery worker/beat.
```powershell
# Start Redis (example)
redis-server

# In another terminal, start Celery worker
celery -A config worker -l info

# In another terminal, start Celery beat for scheduled tasks
celery -A config beat -l info
```

### 3. Frontend Setup
```powershell
cd frontend

# Start development server
npm run dev
```

### 4. Access the Application
- **Frontend:** http://localhost:5173/
- **Backend API:** http://localhost:8000/api/
- **Admin Panel:** http://localhost:8000/admin/

---

## ⚙️ Crawler Configuration

Environment variables (optional):
```
CRAWLER_MAX_PAGES=0        # 0 = no limit (auto)
CRAWLER_USE_SELENIUM=true # true = use Selenium with fallback to requests
CRAWLER_HEADLESS=true     # true = headless browser
```

---

## 📁 Project Structure

```
IR-Netra-Budhathoki/
├── backend/                    # Django Backend
│   ├── config/                # Django project config
│   └── apps/                  # Django apps
│       ├── search/            # Search functionality
│       ├── classification/    # ML classification
│       └── crawler/           # Web crawler
├── frontend/                  # React Frontend
│   └── src/
│       ├── components/        # React components
│       ├── services/          # API service
│       └── types/             # TypeScript types
├── data/                      # Training data
│   └── training_documents.csv
├── requirements.txt           # Python dependencies
└── .env                       # Environment variables
```

---

## 🔗 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/` | GET | API info |
| `/api/search/?query=...` | GET | Search publications |
| `/api/classify/` | POST | Classify text |
| `/api/batch-classify/` | POST | Batch classify texts |
| `/api/model-info/` | GET | Model information |
| `/api/index-info/` | GET | Sample inverted index entries |
| `/api/index-stats/` | GET | Index statistics |
| `/api/crawler-status/` | GET | Crawler status |
| `/api/trigger-crawl/` | POST | Trigger manual crawl |

---

## 🎯 Features

### Search Engine (65 marks)
- ✅ BFS Web Crawler with robots.txt compliance
- ✅ Inverted Index with TF-IDF scoring
- ✅ Query processor with relevance ranking

### Document Classification (25 marks)
- ✅ Naive Bayes classifier
- ✅ K-means clustering
- ✅ 180+ training documents (60+ per category)

### Usability (10 marks)
- ✅ Google Scholar-like interface
- ✅ Responsive design
- ✅ Keyboard shortcuts (Ctrl+K)

---

## 📚 Training Data Sources
Record the source URLs and access dates for the training corpus in `data/sources.md`.

---

## 📦 Technology Stack

| Component | Technology |
|-----------|------------|
| Backend | Django 5.1 + DRF |
| Frontend | React 19 + Vite + TypeScript |
| Database | PostgreSQL 18 |
| ML | scikit-learn |
| NLP | NLTK |
| Task Queue | Celery + Redis |
