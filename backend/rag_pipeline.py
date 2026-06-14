"""RAG pipeline: PDF → chunks → embeddings → Pinecone → retriever → LLM."""

import os

from langchain_community.document_loaders import PyMuPDFLoader
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_pinecone import PineconeVectorStore
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pinecone import Pinecone, ServerlessSpec

from backend import config
from backend.llm import llm


# ---------- Embeddings ----------
embedding_model = HuggingFaceEmbeddings(model_name=config.EMBEDDING_MODEL_NAME)


# ---------- Pinecone index + vector store ----------
def _get_or_create_vector_store() -> PineconeVectorStore:
    """Return a connected PineconeVectorStore, building the index from the FAQ PDF on first run."""
    if not config.PINECONE_API_KEY:
        raise RuntimeError("PINECONE_API_KEY is not set. Add it to your .env file.")

    pc = Pinecone(api_key=config.PINECONE_API_KEY)
    existing = [i["name"] for i in pc.list_indexes()]

    if config.PINECONE_INDEX_NAME not in existing:
        pc.create_index(
            name=config.PINECONE_INDEX_NAME,
            dimension=config.EMBEDDING_DIMENSION,
            metric="cosine",
            spec=ServerlessSpec(cloud=config.PINECONE_CLOUD, region=config.PINECONE_REGION),
        )
        # First-time ingest: PDF → chunks → upsert
        if not os.path.exists(config.KNOWLEDGE_PDF_PATH):
            raise FileNotFoundError(
                f"Pinecone index '{config.PINECONE_INDEX_NAME}' is empty and the FAQ PDF "
                f"was not found at '{config.KNOWLEDGE_PDF_PATH}'. "
                f"Run `python scripts/ingest_pdf.py` first."
            )
        docs = PyMuPDFLoader(config.KNOWLEDGE_PDF_PATH).load()
        chunks = RecursiveCharacterTextSplitter(
            chunk_size=config.RAG_CHUNK_SIZE,
            chunk_overlap=config.RAG_CHUNK_OVERLAP,
        ).split_documents(docs)
        return PineconeVectorStore.from_documents(
            documents=chunks,
            embedding=embedding_model,
            index_name=config.PINECONE_INDEX_NAME,
        )

    return PineconeVectorStore(
        index_name=config.PINECONE_INDEX_NAME,
        embedding=embedding_model,
    )


vector_store = _get_or_create_vector_store()
retriever = vector_store.as_retriever(
    search_type="similarity",
    search_kwargs={"k": config.RAG_TOP_K},
)


# ---------- Chain ----------

RAG_SYSTEM_PROMPT = """You are an Airline Customer Support assistant.
Use ONLY the following retrieved context to answer the user's question about airline policies
and FAQs. If the context does not contain the answer, politely say you do not have that
information and suggest contacting airline support.

Context:
{context}

Be clear, concise, and friendly. Use bullet points where helpful."""


_rag_prompt = ChatPromptTemplate.from_messages([
    ("system", RAG_SYSTEM_PROMPT),
    ("user", "{question}"),
])


def _format_docs(docs):
    return "\n\n".join(d.page_content for d in docs)


rag_chain = (
    {"context": retriever | _format_docs, "question": RunnablePassthrough()}
    | _rag_prompt
    | llm
    | StrOutputParser()
)


# ---------- Fallback chain (for out-of-context queries) ----------

FALLBACK_SYSTEM_PROMPT = """You are an Airline Customer Support assistant. The user has asked a
question that is outside the scope of airline customer support.

Politely respond that you can only help with:
- Flight information (status, schedule, seats, fares)
- Airline policies (baggage, cancellation, refund, check-in)
- FAQs and special assistance (pets, wheelchair, musical instruments)

Encourage the user to ask an airline-related question. Keep it short and friendly."""


_fallback_prompt = ChatPromptTemplate.from_messages([
    ("system", FALLBACK_SYSTEM_PROMPT),
    ("user", "{query}"),
])

fallback_chain = _fallback_prompt | llm | StrOutputParser()
