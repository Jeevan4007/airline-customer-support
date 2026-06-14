"""FastAPI service exposing the airline customer support pipeline as a REST endpoint."""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from api.schemas import QueryRequest, QueryResponse
from backend import airline_support_pipeline_safe

app = FastAPI(
    title="Airline Customer Support API",
    description=(
        "AI-powered airline customer support. The `/ask` endpoint runs the full agentic "
        "pipeline (input guardrail → classifier → SQL/RAG/Fallback → output guardrail) and "
        "returns a JSON response with the answer plus diagnostic information."
    ),
    version="1.0.0",
)


# CORS — wide-open in development so the Streamlit UI can call us from any port.
# Tighten in production by listing specific origins.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root() -> dict:
    return {
        "service": "Airline Customer Support API",
        "status": "running",
        "docs": "/docs",
        "endpoints": {"ask": "POST /ask", "health": "GET /health"},
    }


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/ask", response_model=QueryResponse)
def ask(request: QueryRequest) -> QueryResponse:
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty.")

    try:
        result = airline_support_pipeline_safe(request.query)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Pipeline failure: {e}") from e

    return QueryResponse(**result)


# Allow `python -m api.main` for quick local runs.
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api.main:app", host="0.0.0.0", port=8000, reload=True)
