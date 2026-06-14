"""One-time ingestion: load the FAQ PDF, chunk it, and upsert embeddings to Pinecone.

Usage:
    python scripts/ingest_pdf.py
"""

import sys
from pathlib import Path

# Make `backend` importable when running this script from the repo root
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from langchain_community.document_loaders import PyMuPDFLoader  # noqa: E402
from langchain_pinecone import PineconeVectorStore  # noqa: E402
from langchain_text_splitters import RecursiveCharacterTextSplitter  # noqa: E402
from pinecone import Pinecone, ServerlessSpec  # noqa: E402

from backend import config  # noqa: E402
from backend.rag_pipeline import embedding_model  # noqa: E402


def main() -> None:
    pdf_path = Path(config.KNOWLEDGE_PDF_PATH)
    if not pdf_path.exists():
        sys.exit(
            f"FAQ PDF not found at {pdf_path}. Download it from "
            f"https://raw.githubusercontent.com/MLOPS-test/Artifacts/refs/heads/main/"
            f"datasets/Knowledge_Base_for_Airline_Info_and_FAQs.pdf and place it in data/."
        )

    if not config.PINECONE_API_KEY:
        sys.exit("PINECONE_API_KEY is not set. Add it to your .env file.")

    print(f"Loading {pdf_path} ...")
    docs = PyMuPDFLoader(str(pdf_path)).load()
    print(f"  -> {len(docs)} page documents")

    print(f"Splitting into chunks (size={config.RAG_CHUNK_SIZE}, "
          f"overlap={config.RAG_CHUNK_OVERLAP}) ...")
    chunks = RecursiveCharacterTextSplitter(
        chunk_size=config.RAG_CHUNK_SIZE,
        chunk_overlap=config.RAG_CHUNK_OVERLAP,
    ).split_documents(docs)
    print(f"  -> {len(chunks)} chunks")

    print(f"Connecting to Pinecone (index='{config.PINECONE_INDEX_NAME}', "
          f"region='{config.PINECONE_REGION}') ...")
    pc = Pinecone(api_key=config.PINECONE_API_KEY)
    if config.PINECONE_INDEX_NAME not in [i["name"] for i in pc.list_indexes()]:
        print("  -> creating index ...")
        pc.create_index(
            name=config.PINECONE_INDEX_NAME,
            dimension=config.EMBEDDING_DIMENSION,
            metric="cosine",
            spec=ServerlessSpec(cloud=config.PINECONE_CLOUD, region=config.PINECONE_REGION),
        )

    print("Upserting embeddings ...")
    PineconeVectorStore.from_documents(
        documents=chunks,
        embedding=embedding_model,
        index_name=config.PINECONE_INDEX_NAME,
    )
    print("Done.")


if __name__ == "__main__":
    main()
