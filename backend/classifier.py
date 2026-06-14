"""LLM-based intent classifier that routes a user query to SQL / RAG / Fallback."""

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

from backend.llm import llm


SYSTEM_PROMPT = """You are an intent classifier for an Airline Customer Support System.
Classify the user query into EXACTLY ONE of the following categories:

1. "Need SQL"      - The query needs real-time flight data from the PostgreSQL `flights` table
                     (status, schedule, route, delay, gate, seats, fare, aircraft, etc.).
2. "Non SQL"       - The query is about airline policies / FAQs (baggage, refund, cancellation,
                     check-in, special assistance, pets, prohibited items, ...).
3. "Out of Context" - The query is not related to airline customer support.

Respond with ONLY the category label exactly as shown above
("Need SQL", "Non SQL", or "Out of Context"). No explanations."""


_prompt = ChatPromptTemplate.from_messages([
    ("system", SYSTEM_PROMPT),
    ("user", "{query}"),
])

input_classifier_chain = _prompt | llm | StrOutputParser()


def classify(query: str) -> str:
    """Return the intent label for the given query."""
    return input_classifier_chain.invoke({"query": query}).strip()
