"""Pydantic request/response models for the FastAPI service."""

from typing import Optional

from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    query: str = Field(..., description="The user question in plain English.", min_length=1)

    model_config = {
        "json_schema_extra": {
            "examples": [
                {"query": "What is the status of flight 6E477 on 10 Nov 2026?"},
                {"query": "How much free baggage is allowed for domestic flights?"},
            ]
        }
    }


class QueryResponse(BaseModel):
    query: str
    intent: str
    route: str
    response: str
    output_safe: Optional[bool] = None
    blocked_reason: Optional[str] = None
