"""LangChain SQL agent for read-only PostgreSQL questions."""

from __future__ import annotations

import os
import re
import logging
import warnings
from typing import Any

from google import genai
from google.genai import types


warnings.filterwarnings(
    "ignore",
    message="Direct use of automatic function calling.*",
)
logging.getLogger("google_genai.models").disabled = True


def _schema_description(connection: Any, schema: str) -> str:
    """Read the live table and column metadata for SQL generation."""
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT table_name, column_name, data_type "
            "FROM information_schema.columns "
            "WHERE table_schema = %s ORDER BY table_name, ordinal_position",
            (schema,),
        )
        rows = cursor.fetchall()
    return "\n".join(f"{table}.{column} ({data_type})" for table, column, data_type in rows)


def _extract_sql(text: str) -> str:
    """Extract one SQL statement from plain or fenced model output."""
    match = re.search(r"```(?:sql)?\s*(.*?)```", text, re.IGNORECASE | re.DOTALL)
    sql = match.group(1) if match else text
    sql = sql.strip().rstrip(";").strip()
    if ";" in sql or not re.match(r"^(SELECT|WITH)\b", sql, re.IGNORECASE):
        raise ValueError("The model did not produce a single read-only SQL query.")
    if re.search(
        r"\b(INSERT|UPDATE|DELETE|DROP|ALTER|TRUNCATE|CREATE|GRANT|REVOKE|CALL)\b",
        sql,
        re.IGNORECASE,
    ):
        raise ValueError("Only read-only SQL queries are allowed.")
    return sql


def _generate(client: Any, model: str, prompt: str) -> str:
    response = client.models.generate_content(
        model=model,
        contents=prompt,
        config=types.GenerateContentConfig(temperature=0, max_output_tokens=2048),
    )
    return response.text or ""


def ask_database(question: str) -> str:
    """Answer a natural-language question using the configured PostgreSQL database."""
    database_url = os.environ.get("POSTGRES_DATABASE_URL")
    api_key = os.environ.get("GOOGLE_API_KEY")
    model = os.environ.get("AGENT_MODEL", "gemini-2.5-flash")
    schema = os.environ.get("DB_SCHEMA", "listings")

    if not database_url:
        return "Database is not configured. Set POSTGRES_DATABASE_URL in .env."
    if not api_key:
        return "Database agent is not configured. Set GOOGLE_API_KEY in .env."
    if not question.strip():
        return "Please provide a database question."

    try:
        import psycopg
        from psycopg import sql as psycopg_sql

        client = genai.Client(api_key=api_key)
        postgres_url = database_url.replace("postgresql+psycopg://", "postgresql://")
        with psycopg.connect(postgres_url) as connection:
            schema_info = _schema_description(connection, schema)
            sql_prompt = (
                "Write exactly one PostgreSQL read-only SQL query for the user's "
                "question. Return SQL only, with no markdown. Use only the tables "
                f"and columns listed below in schema {schema!r}.\n\n"
                f"Schema:\n{schema_info}\n\nQuestion: {question}"
            )
            query = _extract_sql(_generate(client, model, sql_prompt))
            with connection.cursor() as cursor:
                cursor.execute(
                    psycopg_sql.SQL("SET search_path TO {}")
                    .format(psycopg_sql.Identifier(schema))
                )
                cursor.execute("SET TRANSACTION READ ONLY")
                cursor.execute(query)
                columns = [description.name for description in cursor.description or []]
                rows = cursor.fetchall()

        result_prompt = (
            "Answer the user's question using only these SQL results. Be concise. "
            f"Question: {question}\nColumns: {columns}\nRows: {rows}"
        )
        return _generate(client, model, result_prompt)
    except Exception as exc:  # noqa: BLE001 - return tool errors to the chat
        return f"Database query failed: {exc}"