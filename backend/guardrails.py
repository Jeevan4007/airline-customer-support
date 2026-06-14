"""Rule-based input / SQL-safety / output guardrails.

These guardrails are intentionally simple and deterministic — they are the cheap first line of
defence and are easy to reason about. In production we would layer an LLM-based safety
classifier on top.
"""

import re
from dataclasses import dataclass


@dataclass
class GuardrailResult:
    safe: bool
    reason: str = ""
    response: str | None = None  # used by the output guardrail to substitute a safe reply


# ---------------- Input guardrail ----------------

UNSAFE_INPUT_PATTERNS: list[str] = [
    r"ignore\s+(all\s+)?previous\s+instructions",
    r"reveal\s+(the\s+)?system\s+prompt",
    r"disregard\s+(all\s+)?previous\s+instructions",
    r"bypass\s+(airport\s+)?security",
    r"jailbreak",
    r"\bdrop\s+table\b",
    r"\bdelete\s+from\b",
    r"\btruncate\b",
    r"\binsert\s+into\b",
    r"\bupdate\s+.+\s+set\b",
    r"export\s+(all|the\s+complete|the\s+entire)?\s*.*database",
    r"show\s+(me\s+)?(all\s+)?customer\s+records",
    r"dump\s+(the\s+)?(entire\s+)?(database|table)",
    r"\bhack\b",
    r"\bweapon\b",
    r"how\s+to\s+(make|build)\s+(a\s+)?bomb",
]


def input_guardrail(query: str) -> GuardrailResult:
    """Validate the user query before any LLM call."""
    if query is None or not query.strip():
        return GuardrailResult(safe=False, reason="Empty query.")
    lowered = query.lower()
    for pattern in UNSAFE_INPUT_PATTERNS:
        if re.search(pattern, lowered):
            return GuardrailResult(
                safe=False,
                reason=f"Blocked by input guardrail (matched: '{pattern}').",
            )
    return GuardrailResult(safe=True)


# ---------------- SQL safety guardrail ----------------

SQL_FORBIDDEN_KEYWORDS: list[str] = [
    "insert", "update", "delete", "drop", "alter",
    "truncate", "create", "grant", "revoke", "merge", "replace",
]
SQL_INJECTION_PATTERNS: list[str] = [
    r";\s*(drop|delete|truncate|alter|insert|update)\b",
    r"--\s",
    r"/\*.*\*/",
]


def sql_safety_guardrail(sql_query: str) -> GuardrailResult:
    """Ensure the generated SQL is a safe read-only SELECT."""
    if not sql_query or not sql_query.strip():
        return GuardrailResult(safe=False, reason="Empty SQL query.")

    sql_lower = sql_query.lower().strip().rstrip(";").strip()

    if not (sql_lower.startswith("select") or sql_lower.startswith("with")):
        return GuardrailResult(safe=False, reason="Only SELECT queries are allowed.")

    for kw in SQL_FORBIDDEN_KEYWORDS:
        if re.search(rf"\b{kw}\b", sql_lower):
            return GuardrailResult(safe=False, reason=f"Forbidden SQL keyword: '{kw}'.")

    for pattern in SQL_INJECTION_PATTERNS:
        if re.search(pattern, sql_lower):
            return GuardrailResult(safe=False, reason="Possible SQL injection detected.")

    return GuardrailResult(safe=True)


# ---------------- Output guardrail ----------------

UNSAFE_OUTPUT_PATTERNS: list[str] = [
    r"\bpassword\b",
    r"\bapi[\s_-]?key\b",
    r"\bcredit[\s-]?card\b",
    r"\bsystem\s+prompt\b",
    r"\bsecret\s+key\b",
]


def output_guardrail(response: str) -> GuardrailResult:
    """Validate the final response before returning it to the user."""
    if response is None:
        return GuardrailResult(
            safe=False,
            reason="Empty response.",
            response="Sorry, I could not generate a response.",
        )

    for pattern in UNSAFE_OUTPUT_PATTERNS:
        if re.search(pattern, response, flags=re.IGNORECASE):
            return GuardrailResult(
                safe=False,
                reason=f"Blocked by output guardrail (matched: '{pattern}').",
                response="I'm sorry, I cannot share that information.",
            )
    return GuardrailResult(safe=True, response=response)
