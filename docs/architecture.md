# Architecture

## Components

| Component | File | Responsibility |
|---|---|---|
| Config | `backend/config.py` | Read env vars, expose typed settings to the rest of the codebase. |
| LLM | `backend/llm.py` | Single shared `ChatOpenAI` instance (Groq or OpenAI). |
| Classifier | `backend/classifier.py` | Route the query: SQL / RAG / Fallback. |
| Database | `backend/database.py` | Connect to Postgres and run a SELECT, return list-of-dicts. |
| SQL pipeline | `backend/sql_pipeline.py` | NL → SQL chain + LangGraph ReAct agent over `sql_execution_tool`. |
| RAG pipeline | `backend/rag_pipeline.py` | PDF → chunks → Pinecone → retriever → LLM. Also fallback chain. |
| Guardrails | `backend/guardrails.py` | Input, SQL-safety, output regex-based checks. |
| Orchestrator | `backend/pipeline.py` | Glues everything together as `airline_support_pipeline_safe`. |
| API | `api/main.py` | FastAPI service exposing `POST /ask`. |
| UI | `ui/streamlit_app.py` | Streamlit chat that talks to the API. |

## Request flow

```
User → Streamlit UI → POST /ask → FastAPI
         ↓
    backend.airline_support_pipeline_safe(query)
         ↓
    1. input_guardrail
    2. classifier
    3a. SQL path:  sql_generation_chain  →  sql_safety_guardrail  →  sql_agent  →  Postgres
    3b. RAG path:  retriever (Pinecone)  →  augmented prompt  →  LLM
    3c. Fallback:  fallback_chain  →  LLM
    4. output_guardrail
         ↓
    JSON {query, intent, route, response, output_safe, blocked_reason}
         ↓
    Streamlit renders the answer + route badge + JSON expander
```

## Why two layers (chain + agent) for SQL?

* The **chain** focuses on a single, well-defined task: write valid PostgreSQL for the `flights`
  schema. Easy to prompt, easy to test, easy to plug a guardrail between it and execution.
* The **agent** is responsible for *running* the tool and *interpreting* the result into a
  human-friendly answer. Separating these concerns gives us a clean place to enforce SQL
  safety, and it makes failures easier to localise (was the SQL wrong, or was the
  summarisation wrong?).

## Why HuggingFace embeddings (not OpenAI)?

Groq does not expose an embeddings endpoint, so we use a free open-source model
(`sentence-transformers/all-MiniLM-L6-v2`, 384-dim). Swap to `OpenAIEmbeddings` and update
`EMBEDDING_DIMENSION` (recreate the Pinecone index) if you have an OpenAI key.

## Defence in depth

1. **Input guardrail** — blocks prompt injection, exfiltration, violence patterns *before*
   any LLM call.
2. **SQL safety guardrail** — only SELECT statements; no DML/DDL/injection patterns.
3. **Output guardrail** — strips responses that leak secrets, API keys, or system prompts.

These are rule-based (cheap, deterministic). In production, layer an LLM-based safety
classifier (e.g. NeMo Guardrails, Lakera) on top.
