"""Thin wrapper over psycopg2 for read-only access to the `flights` Supabase Postgres table."""

from typing import Union

import psycopg2

from backend import config


def execute_sql_query(query: str) -> Union[list[dict], str]:
    """Execute a SELECT SQL query and return the results as a list of dicts.

    On error, returns an error string so the calling agent can react gracefully without
    crashing the request.
    """
    conn = None
    try:
        conn = psycopg2.connect(**config.DB_PARAMS)
        cursor = conn.cursor()
        cursor.execute(query)

        if cursor.description is None:
            cursor.close()
            return "No results returned (the query did not produce a result set)."

        columns = [d[0] for d in cursor.description]
        rows = cursor.fetchall()
        results = [dict(zip(columns, row)) for row in rows]
        cursor.close()
        return results if results else "No matching records found."
    except Exception as e:
        return f"Error executing query: {e}"
    finally:
        if conn is not None:
            conn.close()
