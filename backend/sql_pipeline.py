"""Natural-language → SQL chain plus a LangGraph ReAct agent that executes the SQL
through a custom tool and replies in plain English."""

import re

from langchain_core.messages import HumanMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent

from backend.database import execute_sql_query
from backend.llm import llm


# ---------- SQL generation chain ----------

SQL_SYSTEM_PROMPT = """You are an expert PostgreSQL query generator for an Airline Customer Support System.
Generate ONE valid PostgreSQL SELECT query for the `flights` table.

Schema of the `flights` table:
- id              BIGINT     (primary key)
- flight_no       TEXT       e.g. 'AI695', '6E477'
- airline_code    TEXT       e.g. 'AI', 'SG', 'IX', '6E'
- airline_name    TEXT
- origin          TEXT
- destination     TEXT
- departure_date  DATE       YYYY-MM-DD
- departure_time  TIME
- arrival_date    DATE
- arrival_time    TIME
- status          TEXT       'On Time', 'Delayed', 'Cancelled'
- delay_minutes   INTEGER
- delay_reason    TEXT
- terminal        TEXT
- gate            TEXT
- aircraft_type   TEXT
- seats_total     INTEGER
- seats_booked    INTEGER    (available = seats_total - seats_booked)
- fare_inr        INTEGER

Rules:
1. SELECT statements only. NEVER use INSERT/UPDATE/DELETE/DROP/ALTER/TRUNCATE/CREATE.
2. Use ILIKE for case-insensitive text matching on origin/destination/airline_name.
3. flight_no should match exactly (case-sensitive uppercase).
4. Use 'YYYY-MM-DD' format for date filters.
5. Always include LIMIT 10 unless a single row is targeted.
6. Output ONLY the SQL string — no markdown fences, no explanation."""


_sql_prompt = ChatPromptTemplate.from_messages([
    ("system", SQL_SYSTEM_PROMPT),
    ("user", "{query}"),
])

sql_generation_chain = _sql_prompt | llm | StrOutputParser()


def clean_sql(sql_text: str) -> str:
    """Strip markdown fences and ensure the query ends with a single semicolon."""
    sql_text = sql_text.strip()
    sql_text = re.sub(r"^```(?:sql)?\s*", "", sql_text, flags=re.IGNORECASE)
    sql_text = re.sub(r"```\s*$", "", sql_text)
    return sql_text.strip().rstrip(";") + ";"


# ---------- SQL execution tool (used by the agent) ----------

@tool
def sql_execution_tool(sql_query: str) -> str:
    """Execute a read-only SELECT SQL query on the flights PostgreSQL table and return the results.

    Use this tool whenever you need real-time flight data such as status, schedule, seats, fares,
    or delays.
    """
    return str(execute_sql_query(sql_query))


# ---------- ReAct agent ----------

AGENT_SYSTEM_PROMPT = (
    "You are an Airline Customer Support agent. You will receive the user's original question "
    "and a pre-generated SQL query. Call `sql_execution_tool` with the provided SQL to fetch "
    "data from the `flights` table, then craft a clear, friendly answer. Mention the flight "
    "number, status, timings, gate, and any delay/cancellation reason whenever relevant. "
    "If the tool returns no records, politely tell the user that no matching flight was found. "
    "Never expose raw SQL or internal errors in the final response."
)


sql_agent = create_react_agent(
    model=llm,
    tools=[sql_execution_tool],
    prompt=AGENT_SYSTEM_PROMPT,
)


def run_sql_agent(user_query: str, sql_query: str) -> str:
    """Run the SQL agent end-to-end and return the final assistant message."""
    agent_input = (
        f"User Question: {user_query}\n"
        f"Generated SQL Query: {sql_query}\n\n"
        "Use the sql_execution_tool with the SQL above and answer the user clearly."
    )
    result = sql_agent.invoke({"messages": [HumanMessage(content=agent_input)]})
    return result["messages"][-1].content
