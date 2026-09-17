"""LangChain SQL agent for read-only PostgreSQL questions."""

from __future__ import annotations

import os
from functools import lru_cache
from typing import Any


@lru_cache(maxsize=4)
def _build_sql_agent(
    database_url: str, model: str, api_key: str, schema: str
) -> Any:
    """Build one SQL agent per database/model configuration."""
    from langchain_community.agent_toolkits import SQLDatabaseToolkit, create_sql_agent
    from langchain_community.utilities import SQLDatabase
    from langchain_google_genai import ChatGoogleGenerativeAI

    database = SQLDatabase.from_uri(database_url, schema=schema)
    llm = ChatGoogleGenerativeAI(
        model=model,
        temperature=0,
        google_api_key=api_key,
    )
    toolkit = SQLDatabaseToolkit(db=database, llm=llm)
    return create_sql_agent(
        llm=llm,
        toolkit=toolkit,
        agent_type="tool-calling",
        verbose=False,
        prefix=(
            "You are a read-only PostgreSQL analyst. Never INSERT, UPDATE, "
            "DELETE, DROP, ALTER, TRUNCATE, or modify database state. "
            f"The active PostgreSQL schema is {schema!r}. Always inspect and "
            "query tables in that schema, using schema-qualified names when "
            "needed. Only answer using SQL queries and the data returned by "
            "the database."
        ),
    )


def _extract_output(result: Any) -> str:
    """Convert plain or provider-structured agent output to readable text."""
    output = result.get("output", result) if isinstance(result, dict) else result
    if isinstance(output, str):
        return output
    if isinstance(output, list):
        text_parts = [
            item.get("text", "")
            for item in output
            if isinstance(item, dict) and isinstance(item.get("text"), str)
        ]
        if text_parts:
            return "".join(text_parts)
    return str(output)


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
        result = _build_sql_agent(database_url, model, api_key, schema).invoke(
            {"input": question}
        )
        return _extract_output(result)
    except Exception as exc:  # noqa: BLE001 - return tool errors to the chat
        return f"Database query failed: {exc}"