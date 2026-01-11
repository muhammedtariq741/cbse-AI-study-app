# CBSE AI Study App

An AI-powered study assistant for CBSE Class 9 students using RAG (Retrieval Augmented Generation) with Google Gemini.

## Features

- 📚 NCERT-aligned answers with board exam formatting
- 🎯 Mark-based response structuring (1, 2, 3, 5 marks)
- 🔍 Intelligent retrieval from CBSE content
- ✨ Gemini-tuned for CBSE examination style

## Tech Stack

- **Backend**: FastAPI (Python)
- **LLM**: Google Gemini 2.0 Flash (tuned)
- **Embeddings**: Gemini text-embedding-004
- **Vector DB**: FAISS (local) / Pinecone (production)
- **Frontend**: Next.js

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- Google Cloud account with Gemini API access

### Backend Setup

```bash
cd backend
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
cp .env.example .env
# Add your GEMINI_API_KEY to .env
uvicorn app.main:app --reload
```

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

## Project Structure

```
studyapp/
├── backend/          # FastAPI Python backend
│   ├── app/          # Application code
│   └── data/         # PDFs, embeddings, tuning data
├── frontend/         # Next.js frontend
└── README.md
```

## Environment Variables

| Variable | Description |
|----------|-------------|
| `GEMINI_API_KEY` | Google Gemini API key |
| `GCP_PROJECT_ID` | Google Cloud project ID |
| `TUNED_MODEL_NAME` | Name of tuned Gemini model (after tuning) |

## License

MIT
