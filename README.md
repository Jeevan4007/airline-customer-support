# Airline Customer Support System

AI-powered airline customer support that answers passenger queries by combining a **LangChain/LangGraph agent**, a **PostgreSQL flights database**, a **Pinecone RAG knowledge base**, and **rule-based guardrails** — exposed as a **FastAPI** service and a **Streamlit** chat UI.

Built as part of the IISc & TalentSprint Advanced Certification in Agentic and Generative AI (Mini-Project 4).

---

## Architecture

```
                  ┌───────────────┐
   user query ───►│ Input         │── unsafe ──► blocked response
                  │ Guardrail     │
                  └──────┬────────┘
                         ▼
                  ┌───────────────┐
                  │ LLM           │
                  │ Classifier    │
                  └──┬─────┬────┬─┘
        "Need SQL"   │     │    │  "Out of Context"
                     │     │    │
                     ▼     ▼    ▼
        ┌──────────────┐ ┌────────────┐ ┌─────────────┐
        │ SQL chain +  │ │ RAG chain  │ │ Fallback    │
        │ SQL safety + │ │ (Pinecone) │ │ chain       │
        │ Postgres     │ │            │ │             │
        └──────┬───────┘ └──────┬─────┘ └──────┬──────┘
               └────────────────┴──────────────┘
                                ▼
                       ┌────────────────┐
                       │ Output         │
                       │ Guardrail      │
                       └────────┬───────┘
                                ▼
                          user response
```

---

## Repository layout

```
airline-customer-support/
├── README.md
├── requirements.txt
├── .env.example
├── .gitignore
├── .devcontainer/devcontainer.json     # GitHub Codespaces config
├── .github/workflows/ci.yml            # CI (lint + pytest)
├── backend/
│   ├── config.py                       # env-var driven settings
│   ├── llm.py                          # ChatOpenAI / Groq init
│   ├── classifier.py                   # input intent classifier
│   ├── database.py                     # psycopg2 helper + execute_sql_query
│   ├── sql_pipeline.py                 # SQL chain + ReAct agent
│   ├── rag_pipeline.py                 # PDF loader → Pinecone vector store
│   ├── guardrails.py                   # input / SQL / output guardrails
│   └── pipeline.py                     # orchestrator (airline_support_pipeline_safe)
├── api/
│   ├── main.py                         # FastAPI service
│   └── schemas.py                      # Pydantic request/response models
├── ui/
│   └── streamlit_app.py                # Streamlit chat UI
├── data/
│   └── README.md                       # how to obtain the CSV and PDF
├── scripts/
│   ├── load_flights_csv.py             # one-time: CSV → Postgres
│   └── ingest_pdf.py                   # one-time: PDF → Pinecone
├── tests/
│   ├── test_guardrails.py
│   └── test_pipeline.py
├── notebooks/                          # original development notebook
└── docs/
    └── architecture.md
```

---

## Quick start — GitHub Codespaces

1. Push this repo to GitHub.
2. Click **Code → Codespaces → Create codespace on main**.
3. The devcontainer installs all dependencies automatically.
4. Copy `.env.example` to `.env` and fill in the keys/credentials.
5. One-time data setup:
   ```bash
   python scripts/load_flights_csv.py
   python scripts/ingest_pdf.py
   ```
6. **Terminal 1** — start the API:
   ```bash
   uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
   ```
7. **Terminal 2** — start the UI:
   ```bash
   streamlit run ui/streamlit_app.py --server.port 8501 --server.address 0.0.0.0
   ```
8. Codespaces auto-forwards ports `8000` (API + Swagger at `/docs`) and `8501` (UI).

---

## Quick start — local

```bash
git clone <this-repo>.git
cd airline-customer-support
python -m venv .venv && source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env       # then edit .env with your keys
python scripts/load_flights_csv.py
python scripts/ingest_pdf.py
uvicorn api.main:app --reload      # terminal 1
streamlit run ui/streamlit_app.py  # terminal 2
```

Open `http://localhost:8501` for the chat UI and `http://localhost:8000/docs` for the API docs.

---

## Environment variables

See `.env.example`. The system supports either **Groq** (free tier, default) or **OpenAI**:

| Variable | Required | Description |
|---|---|---|
| `GROQ_API_KEY` | one of the two | Groq API key for `openai/gpt-oss-120b` |
| `OPENAI_API_KEY` | one of the two | OpenAI key (overrides Groq if set) |
| `PINECONE_API_KEY` | yes | Pinecone account API key |
| `PINECONE_INDEX_NAME` | no | Default `airline-faq-index` |
| `PINECONE_CLOUD` / `PINECONE_REGION` | no | Defaults to `aws` / `us-east-1` |
| `PGHOST`, `PGPORT`, `PGUSER`, `PGPASSWORD`, `PGDATABASE` | yes | Supabase / PostgreSQL connection |
| `PGSSLMODE` | no | Defaults to `require` (needed for Supabase) |

---

## API

`POST /ask`

```jsonc
// request
{ "query": "What is the status of flight 6E477 on 10 Nov 2026?" }

// response
{
  "query":   "What is the status of flight 6E477 on 10 Nov 2026?",
  "intent":  "Need SQL",
  "route":   "SQL",
  "response": "Flight 6E477 is currently delayed by 25 minutes ...",
  "output_safe": true,
  "blocked_reason": null
}
```

Other endpoints: `GET /` (info), `GET /health` (health check), Swagger UI at `/docs`.

---

## Testing

```bash
pytest -v
```

`tests/test_guardrails.py` covers the rule-based guardrails (pure functions, no API needed).
`tests/test_pipeline.py` is an integration smoke test that requires a configured `.env`.

---

## License

MIT
