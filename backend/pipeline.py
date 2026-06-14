"""End-to-end orchestrator: input guardrail → classifier → (SQL | RAG | Fallback) → output guardrail."""

from typing import TypedDict

from backend.classifier import classify
from backend.guardrails import (
    input_guardrail,
    output_guardrail,
    sql_safety_guardrail,
)


class PipelineResult(TypedDict, total=False):
    query: str
    intent: str
    route: str
    response: str
    output_safe: bool
    blocked_reason: str | None


def airline_support_pipeline_safe(user_query: str) -> PipelineResult:
    """Run the safe end-to-end pipeline and return a diagnostic-rich dict."""
    # 1. Input guardrail — block unsafe queries before any LLM call
    ig = input_guardrail(user_query)
    if not ig.safe:
        return PipelineResult(
            query=user_query,
            intent="BLOCKED (input guardrail)",
            route="Input Guardrail",
            response=(
                "Your request was blocked by our safety checks and cannot be processed. "
                "Please rephrase your question to focus on airline-related topics."
            ),
            output_safe=True,
            blocked_reason=ig.reason,
        )

    # 2. Classify intent
    intent = classify(user_query)

    # 3. Route based on classification
    if "Need SQL" in intent:
        # Lazy import so unit tests that don't need the SQL stack run faster
        from backend.sql_pipeline import (
            clean_sql,
            run_sql_agent,
            sql_generation_chain,
        )

        raw_sql = clean_sql(sql_generation_chain.invoke({"query": user_query}))
        sql_safe = sql_safety_guardrail(raw_sql)
        if not sql_safe.safe:
            response = (
                "I cannot run that query because it failed our SQL safety checks. "
                f"({sql_safe.reason}) Please ask a simple read-only flight question."
            )
            route = "SQL (blocked by guardrail)"
        else:
            response = run_sql_agent(user_query, raw_sql)
            route = "SQL"

    elif "Non SQL" in intent:
        from backend.rag_pipeline import rag_chain
        response = rag_chain.invoke(user_query)
        route = "RAG"

    else:
        from backend.rag_pipeline import fallback_chain
        response = fallback_chain.invoke({"query": user_query})
        route = "Fallback"

    # 4. Output guardrail
    og = output_guardrail(response)

    return PipelineResult(
        query=user_query,
        intent=intent,
        route=route,
        response=og.response,
        output_safe=og.safe,
        blocked_reason=og.reason if not og.safe else None,
    )
