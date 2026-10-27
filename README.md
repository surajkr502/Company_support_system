# BigCompany Knowledge Assistant

An Agentic RAG (Retrieval-Augmented Generation) chatbot that answers employee questions about company policies, engineering guidelines, and onboarding. It is built with **LangGraph** and **FastAPI** on the backend, **Next.js** on the frontend, and **Google Gemini** for embeddings and text generation.

## Features

- **Chat interface** for asking questions in plain English
- **Agentic RAG workflow** built with LangGraph: retrieve, grade, generate, or rewrite the query and retry
- **Document grading** with an LLM, so only relevant context reaches the answer
- **Query rewriting** when no document matches, capped at a maximum number of retries
- **Greeting shortcut** so simple messages like "hi" get an instant reply without calling the LLM
- **Source-grounded answers** that rely only on the company documents

## Tech Stack

| Layer | Technology |
|-------|------------|
| Frontend | Next.js 16 (Pages Router), React 19, CSS Modules |
| Backend API | FastAPI, Uvicorn |
| Agent workflow | LangGraph, LangChain Core |
| LLM | Google Gemini (`gemini-3.8-flash` by default) |
| Embeddings | Google Gemini (`gemini-embedding-001` by default) |
| Vector store | LangChain `InMemoryVectorStore` |

## How It Works

```
User types a question in the browser
        │
        ▼
Frontend (Next.js) sends POST /ask to the backend
        │
        ▼
Backend runs the LangGraph workflow:
  retrieve → grade_documents
        │
        ├── at least one relevant document → generate → answer
        │
        └── no relevant documents → transform_query → retrieve (max 2 times)
        │
        ▼
Backend returns { "answer": "...", "question": "..." }
        │
        ▼
Frontend displays the answer in the chat
```

## Project Structure

```
Company_support_system/
├── backend/
│   ├── main.py              # FastAPI app, CORS configuration, router registration
│   ├── graph.py             # Knowledge base, Gemini LLM, and LangGraph workflow
│   ├── routers/
│   │   └── rag.py           # POST /ask endpoint
│   ├── list_model.py        # Helper script to list models available to your API key
│   ├── requirements.txt
│   └── .env                 # Secrets (not committed)
└── frontend/
    ├── components/
    │   ├── chat.js          # Chat UI and API calls
    │   └── layout.js        # Page layout and title
    ├── pages/
    │   ├── _app.js
    │   ├── _document.js
    │   └── index.js         # Home page
    ├── styles/
    │   ├── globals.css
    │   ├── layout.module.css
    │   └── chat.module.css
    ├── .env                 # Backend URL (not committed)
    ├── jsconfig.json
    ├── next.config.mjs
    └── package.json
```

## Prerequisites

- **Python 3.10+**
- **Node.js 18.18+** (LTS recommended) and npm
- A **Google Gemini API key** from [Google AI Studio](https://aistudio.google.com/)

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/surajkr502/Company_support_system.git
cd Company_support_system
```

### 2. Backend setup

```bash
cd backend
python -m venv ../.venv

# Windows (PowerShell)
..\.venv\Scripts\Activate.ps1

# macOS / Linux
source ../.venv/bin/activate

pip install -r requirements.txt
```

Create a file named `.env` inside `backend/`:

```env
GEMINI_API_KEY=your-gemini-api-key
GEMINI_CHAT_MODEL=gemini-3.8-flash
GEMINI_EMBED_MODEL=gemini-embedding-001
```

To see which models your API key can use, run:

```bash
python list_model.py
```

Start the backend:

```bash
uvicorn main:app --reload
```

The API runs at `http://127.0.0.1:8000`. Interactive docs are at `http://127.0.0.1:8000/docs`.

### 3. Frontend setup

Open a second terminal:

```bash
cd frontend
npm install
```

Create a file named `.env` inside `frontend/`:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

Start the frontend:

```bash
npm run dev
```

Open `http://localhost:3000` in your browser.

## Environment Variables

| Variable | Location | Required | Default | Description |
|----------|----------|----------|---------|-------------|
| `GEMINI_API_KEY` | `backend/.env` | Yes | None | Google Gemini API key. Never commit this. |
| `GEMINI_CHAT_MODEL` | `backend/.env` | No | `gemini-3.8-flash` | Model used for grading, rewriting, and answering |
| `GEMINI_EMBED_MODEL` | `backend/.env` | No | `gemini-embedding-001` | Model used to embed documents and queries |
| `NEXT_PUBLIC_API_URL` | `frontend/.env` | Yes | None | Backend base URL, e.g. `http://localhost:8000` |

Use model names without the `models/` prefix.

## API Reference

| Method | Endpoint | Request Body | Response |
|--------|----------|--------------|----------|
| GET | `/` | None | `{"message": "BigCompany Agentic RAG API is running!"}` |
| POST | `/ask` | `{"question": "string"}` | `{"answer": "string", "question": "string"}` |

Example:

```bash
curl -X POST http://127.0.0.1:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "What is the remote work policy?"}'
```

## Knowledge Base

The company documents are defined directly in `backend/graph.py` as a list of LangChain `Document` objects. They cover:

- Remote work policy
- Vacation (PTO) policy
- Travel reimbursement policy
- Code review policy
- Deployment security requirements
- Product roadmap Q1 2026
- New employee onboarding

To add or change content, edit `company_documents` in `graph.py` and restart the backend. The vector store is built in memory at startup, so there is no database to migrate.

## Customization

- **Change the model:** Update `GEMINI_CHAT_MODEL` in `backend/.env`. Run `python list_model.py` to see available options.
- **Change the number of retrieved documents:** Edit `search_kwargs={"k": 2}` in `graph.py`.
- **Change the retry limit:** Edit `MAX_REWRITES` in `graph.py`.
- **Change the greeting shortcut:** Edit the `GREETINGS` set in `backend/routers/rag.py`.

## Troubleshooting

| Problem | Likely cause and fix |
|---------|----------------------|
| `NOT_FOUND` / 404 for a model | The model is unavailable for your key. Run `python list_model.py` and update `.env`. |
| `429 RESOURCE_EXHAUSTED` | Gemini free-tier rate limit reached. Wait a minute and ask one question at a time. |
| `500 INTERNAL` during embedding | Temporary Gemini server error. Retry, or switch `GEMINI_EMBED_MODEL` to another embedding model. |
| "Could not connect to the server" in the UI | Backend is not running, or `NEXT_PUBLIC_API_URL` is wrong. |
| `OPTIONS /ask 400` in backend logs | CORS. Make sure your frontend origin is listed in `allow_origins` in `main.py`. |
| `NameError` when starting the backend | `graph.py` is incomplete. Make sure every section is defined in order. |
| Frontend ignores `.env` changes | Restart `npm run dev` after editing `.env`. |

## Known Limitations

- The knowledge base is stored in memory, so documents are re-embedded every time the backend starts.
- Each question makes several Gemini API calls (one per retrieved document for grading, plus generation), so free-tier rate limits can be reached quickly.
- The app does not have user authentication or chat history.
- Answers are only as good as the documents provided. This is a demo, not a production system.

## Security Notes

- Never commit `.env` files. Add them to `.gitignore`.
- Never put the Gemini API key in frontend code or in any variable prefixed with `NEXT_PUBLIC_`. Those values are visible in the browser.
- Rotate your API key if it was ever committed or shared.

## Roadmap

- Load documents from files (PDF, Markdown) instead of hard-coded text
- Persist the vector store (e.g., FAISS or Chroma)
- Add user authentication and per-user chat history
- Show source document citations in the UI
- Add streaming responses
