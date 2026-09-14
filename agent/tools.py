"""
tools.py
--------
Tool registry. Each tool's description (what it does / when to call
it — the text the LLM sees) lives in tools/<name>.md, loaded via
AgentConfig. This file only maps a tool name to its Python
implementation and builds the Gemini-format schema — mechanics only.

To add a tool:
  1. Write tools/<name>.md describing what it does / when to use it.
  2. Implement a Python function below.
  3. Register it in IMPLEMENTATIONS.
A tool is only exposed to the LLM if it has both a .md doc AND an
entry in IMPLEMENTATIONS.
"""

from __future__ import annotations
from typing import Any, Callable

from google.genai import types

from agent.config import AgentConfig


def _search_tool(query: str) -> str:
    """Placeholder implementation. Replace with a real search call."""
    return f"(stub) search results for: {query}"


def _calculator_tool(expression: str) -> str:
    """Placeholder implementation. Replace with a safe eval / math lib."""
    try:
        # NOTE: MVP stub only — do not use eval() on untrusted input in
        # production. Swap for a safe expression parser (e.g. `numexpr`
        # or a proper math grammar) before this leaves MVP.
        result = eval(expression, {"__builtins__": {}})
        return str(result)
    except Exception as e:  # noqa: BLE001 - MVP stub
        return f"error evaluating expression: {e}"


# name -> (python implementation, JSON schema for its input parameters)
IMPLEMENTATIONS: dict[str, tuple[Callable[..., Any], dict[str, Any]]] = {
    "search": (
        _search_tool,
        {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "What to search for"},
            },
            "required": ["query"],
        },
    ),
    "calculator": (
        _calculator_tool,
        {
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",
                    "description": "A math expression to evaluate, e.g. '2 + 2 * 3'",
                },
            },
            "required": ["expression"],
        },
    ),
}


def get_tool_schemas(config: AgentConfig) -> list[types.Tool]:
    """Gemini-format tool declarations for every tool with both a .md
    doc (config.tool_docs) and a Python implementation."""
    declarations = []
    for name, description in config.tool_docs.items():
        if name not in IMPLEMENTATIONS:
            continue
        _, parameters = IMPLEMENTATIONS[name]
        declarations.append(
            types.FunctionDeclaration(
                name=name,
                description=description,
                parameters=parameters,
            )
        )
    if not declarations:
        return []
    return [types.Tool(function_declarations=declarations)]


def call_tool(name: str, tool_input: dict[str, Any]) -> Any:
    if name not in IMPLEMENTATIONS:
        raise ValueError(f"Unknown tool: {name}")
    func, _ = IMPLEMENTATIONS[name]
    return func(**tool_input)
