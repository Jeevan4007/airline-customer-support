"""Centralised environment-variable driven settings for the backend."""

import os
from dotenv import load_dotenv

load_dotenv()


# ---------------- LLM ----------------
GROQ_API_KEY: str | None = os.getenv("GROQ_API_KEY")
OPENAI_API_KEY: str | None = os.getenv("OPENAI_API_KEY")
LLM_MODEL: str = os.getenv(
    "LLM_MODEL",
    "gpt-4o-mini" if OPENAI_API_KEY else "openai/gpt-oss-120b",
)
LLM_TEMPERATURE: float = float(os.getenv("LLM_TEMPERATURE", "0"))


# ---------------- Pinecone ----------------
PINECONE_API_KEY: str | None = os.getenv("PINECONE_API_KEY")
PINECONE_INDEX_NAME: str = os.getenv("PINECONE_INDEX_NAME", "airline-faq-index")
PINECONE_CLOUD: str = os.getenv("PINECONE_CLOUD", "aws")
PINECONE_REGION: str = os.getenv("PINECONE_REGION", "us-east-1")


# ---------------- Embeddings ----------------
EMBEDDING_MODEL_NAME: str = os.getenv(
    "EMBEDDING_MODEL_NAME",
    "text-embedding-3-small",
)
EMBEDDING_DIMENSION: int = int(os.getenv("EMBEDDING_DIMENSION", "1536"))


# ---------------- PostgreSQL ----------------
DB_PARAMS: dict[str, str] = {
    "host":     os.getenv("PGHOST", ""),
    "port":     os.getenv("PGPORT", "5432"),
    "user":     os.getenv("PGUSER", ""),
    "password": os.getenv("PGPASSWORD", ""),
    "dbname":   os.getenv("PGDATABASE", "postgres"),
    "sslmode":  os.getenv("PGSSLMODE", "require"),
}


# ---------------- Data files ----------------
FLIGHTS_CSV_PATH: str = os.getenv(
    "FLIGHTS_CSV_PATH",
    "data/Flights_Schedule_Data_v1.csv",
)
KNOWLEDGE_PDF_PATH: str = os.getenv(
    "KNOWLEDGE_PDF_PATH",
    "data/Knowledge_Base_for_Airline_Info_and_FAQs.pdf",
)


# ---------------- RAG tuning ----------------
RAG_CHUNK_SIZE: int = int(os.getenv("RAG_CHUNK_SIZE", "800"))
RAG_CHUNK_OVERLAP: int = int(os.getenv("RAG_CHUNK_OVERLAP", "100"))
RAG_TOP_K: int = int(os.getenv("RAG_TOP_K", "4"))
