# AI Presentation Avatar SaaS Platform

A comprehensive SaaS platform for creating personalized presentation avatars with multi-language support, custom avatar selection, regional voice options, and document-based presentation generation.

## Features

- **User Authentication**: Google OAuth + Email/Password with email verification
- **Document Upload**: Support for PDF, PPT, DOCX files
- **Multi-Language Support**: 8+ languages including English (UK/US), Hindi, Telugu, Portuguese, Japanese, Chinese
- **Avatar Customization**: Multiple 3D avatar options (Male/Female)
- **Regional Voice Options**: Gender and region-specific voice selections
- **Custom Voice Upload**: Users can upload their own voice samples
- **Agentic Presentation Generation**: AI-powered extraction and presentation creation
- **API Keys & Rate Limiting**: Developer-friendly API with quota management
- **Isolated Presentations**: Per-user secure presentation instances

## Tech Stack

**Backend**: FastAPI + PostgreSQL + SQLAlchemy
**Frontend**: Next.js 14 (React)
**Authentication**: Supabase Auth (Google OAuth + Email)
**LLM**: Anthropic Claude
**Vector DB**: Pinecone / Supabase pgvector
**Voice Synthesis**: ElevenLabs
**3D Avatars**: Ready Player Me / D-ID API
**Deployment**: Vercel (Frontend) + Railway/Render (Backend)

## Project Structure

```
├── backend/              # FastAPI backend application
│   ├── main.py
│   ├── config.py
│   ├── api/
│   │   ├── auth.py       # Authentication endpoints
│   │   ├── presentations.py
│   │   ├── avatars.py
│   │   ├── voices.py
│   │   └── api_keys.py
│   ├── core/
│   │   ├── security.py
│   │   └── config.py
│   ├── db/
│   │   ├── models.py     # SQLAlchemy models
│   │   ├── schemas.py    # Pydantic schemas
│   │   └── database.py
│   ├── services/
│   │   ├── auth_service.py
│   │   ├── document_processor.py
│   │   ├── agentic_pipeline.py
│   │   ├── avatar_service.py
│   │   └── voice_service.py
│   ├── utils/
│   │   ├── validators.py
│   │   └── helpers.py
│   └── migrations/       # Alembic database migrations
├── frontend/             # Next.js frontend application
│   ├── app/
│   ├── components/
│   ├── lib/
│   ├── public/
│   └── styles/
├── docs/                 # API Documentation
├── requirements.txt      # Python dependencies
└── .env.example         # Environment template
```

## Setup Instructions

### Prerequisites
- Python 3.10+
- Node.js 18+
- PostgreSQL 14+
- Accounts: Supabase, Anthropic, ElevenLabs, Pinecone

### Backend Setup

```bash
# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Setup database
alembic upgrade head

# Run server
uvicorn backend.main:app --reload
```

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

## Environment Configuration

Copy `.env.example` to `.env` and fill in all required API keys and configuration values.

## API Documentation

API docs available at `http://localhost:8000/docs` (FastAPI Swagger UI)

## Development Status

**Phase 1**: User authentication & profile system
**Phase 2**: Presentation document upload & storage
**Phase 3**: Avatar customization UI
**Phase 4**: Multi-language & voice integration
**Phase 5**: API key system & rate limiting
**Phase 6**: Agentic presentation generation
**Phase 7**: Deployment & scaling

---

*AI Presentation Avatar Platform - Building the future of automated presentations*
