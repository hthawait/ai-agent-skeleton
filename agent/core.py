"""
core.py
-------
The Agent class: orchestration only. It assembles the system prompt
from markdown (via AgentConfig), runs the message loop against Gemini,
and dispatches function/tool calls. No domain rules, personas, skills,
or tool logic live here — all of that is data, loaded from .md files.
"""

from __future__ import annotations
from typing import Any

from google.genai import types

from agent.config import AgentConfig
from agent.llm import LLMClient
from agent.tools import get_tool_schemas, call_tool


class Agent:
    def __init__(self, config: AgentConfig | None = None, llm: LLMClient | None = None):
        self.config = config or AgentConfig.load()
        self.llm = llm or LLMClient()
        self.system_prompt = self.config.build_system_prompt()
        self.tools = get_tool_schemas(self.config)
        self.contents: list[types.Content] = []

    def reset(self) -> None:
        self.contents = []

    def run(self, user_input: str, max_tool_iterations: int = 5) -> str:
        """Send a user message, resolve any function calls, return final text."""
        self.contents.append(
            types.Content(role="user", parts=[types.Part(text=user_input)])
        )

        for _ in range(max_tool_iterations):
            response = self.llm.create_message(
                system=self.system_prompt,
                contents=self.contents,
                tools=self.tools,
            )

            candidate = response.candidates[0]
            self.contents.append(candidate.content)

            function_calls = [
                part.function_call for part in candidate.content.parts if part.function_call
            ]

            if not function_calls:
                return self._extract_text(candidate.content.parts)

            response_parts = []
            for fc in function_calls:
                result = call_tool(fc.name, dict(fc.args or {}))
                response_parts.append(
                    types.Part(
                        function_response=types.FunctionResponse(
                            name=fc.name,
                            response={"result": result},
                        )
                    )
                )

            self.contents.append(types.Content(role="user", parts=response_parts))

        return "(max tool iterations reached without a final answer)"

    @staticmethod
    def _extract_text(parts: list[Any]) -> str:
        return "".join(part.text for part in parts if getattr(part, "text", None))
