# Crop Doctor AI 🌿

An AI-powered crop leaf disease diagnostic tool built with **Streamlit**, **Django REST Framework**, and **Groq's Multimodal Vision AI** (`qwen/qwen3.8-27b`).

---

## 🚀 Live Deployment on Render (Docker)

You can deploy Crop Doctor AI as a single Docker container on **[Render](https://render.com/)** in minutes.

### Method 1: Using Render Dashboard (Recommended)

1. Sign in to your [Render Dashboard](https://dashboard.render.com/).
2. Click **New +** → **Web Service**.
3. Connect your GitHub repository: `https://github.com/Ayush-46-06/crop-doctor`.
4. Configure the service settings:
   - **Name**: `crop-doctor-ai` (or your choice)
   - **Region**: Choose the region closest to you (e.g., Oregon, Frankfurt, Singapore)
   - **Branch**: `main` (or `master`)
   - **Runtime**: **Docker**
   - **Instance Type**: **Free** (or Starter)
5. Under **Environment Variables**, add:
   | Key | Value | Description |
   |---|---|---|
   | `GROQ_API_KEY` | `gsk_...` | Your Groq API key from [console.groq.com](https://console.groq.com) |
   | `GROQ_MODEL` | `qwen/qwen3.8-27b` | Multimodal vision model |
   | `DJANGO_SECRET_KEY` | *(Click "Generate")* | Random secure string |
   | `DJANGO_DEBUG` | `False` | Production mode |
   | `DJANGO_ALLOWED_HOSTS` | `127.0.0.1,localhost,0.0.0.0,.onrender.com,*` | Allowed domain hosts |
   | `API_URL` | `http://127.0.0.1:8000/api/analyze/` | Internal communication URL |
   | `PORT` | `8501` | Exposed web port |
6. Click **Create Web Service**. Render will automatically build the Docker image and deploy your web app!

---

### Method 2: Using Render Blueprint (`render.yaml`)

This repository includes a `render.yaml` file. In Render:
1. Click **New +** → **Blueprint**.
2. Select your repository.
3. Render will read `render.yaml`, preconfigure the service, generate a `DJANGO_SECRET_KEY`, and prompt you to input your `GROQ_API_KEY`.
4. Click **Apply**.

---

## 🐳 Run Locally with Docker

### 1. Using Docker Compose
Make sure Docker Desktop is running and you have your `.env` configured:
```bash
# Build and start both Django backend & Streamlit frontend
docker compose up --build
```
- **Streamlit Web UI**: [http://localhost:8501](http://localhost:8501)
- **Django REST API**: [http://localhost:8000/api/health/](http://localhost:8000/api/health/)

To stop:
```bash
docker compose down
```

### 2. Using Single-Container Docker Run
```bash
# Build the Docker image
docker build -t crop-doctor-ai .

# Run container (matches Render's single-container environment)
docker run -p 8501:8501 -p 8000:8000 --env-file .env crop-doctor-ai
```

---

## 💻 Run Locally without Docker (Python 3.10+)

### Windows (PowerShell)
```powershell
# 1. Create and activate virtual environment
python -m venv .venv
.venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Create .env from template
copy .env.example .env
# Edit .env and paste your GROQ_API_KEY

# 4. Run database migrations
python manage.py migrate

# 5. Terminal 1: Start Django Backend
python manage.py runserver 127.0.0.1:8000

# 6. Terminal 2: Start Streamlit Frontend
streamlit run streamlit_app.py
```

### macOS / Linux
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python manage.py migrate
python manage.py runserver 127.0.0.1:8000
# In a second terminal:
streamlit run streamlit_app.py
```

---

## 🛠️ Tech Stack & Architecture

- **Frontend**: Streamlit (File upload, Camera capture, Responsive report display)
- **Backend**: Django & Django REST Framework (Image validation, preprocessing, error handling)
- **Production Server**: Gunicorn WSGI server + Streamlit Web server
- **AI Engine**: Groq Cloud API with `qwen/qwen3.8-27b` multimodal vision model
- **Containerization**: Docker & Docker Compose

---

## ⚠️ Limitations & Educational Disclaimer

This is an educational prototype. Multimodal visual AI describes visible leaf symptoms and patterns but is **not** a laboratory-certified agricultural diagnostic test. 

Do not apply chemical pesticides or treatments based solely on AI output. Always verify symptoms with a certified agronomist or local agricultural extension office.
