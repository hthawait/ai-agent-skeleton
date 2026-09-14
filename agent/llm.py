"""
llm.py
------
Thin wrapper around Google's Gemini API (google-genai SDK). Pure
plumbing — no business logic.
"""

from __future__ import annotations
import os
from typing import Any

from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

DEFAULT_MODEL = os.environ.get("AGENT_MODEL", "gemini-2.5-flash")
DEFAULT_MAX_TOKENS = int(os.environ.get("AGENT_MAX_TOKENS", "2048"))


class LLMClient:
    def __init__(self, model: str = DEFAULT_MODEL, max_tokens: int = DEFAULT_MAX_TOKENS):
        api_key = os.environ.get("GOOGLE_API_KEY")
        self.client = genai.Client(api_key=api_key)
        self.model = model
        self.max_tokens = max_tokens

    def create_message(
        self,
        system: str,
        contents: list[types.Content],
        tools: list[types.Tool] | None = None,
    ) -> types.GenerateContentResponse:
        config = types.GenerateContentConfig(
            system_instruction=system,
            max_output_tokens=self.max_tokens,
            tools=tools or None,
        )
        return self.client.models.generate_content(
            model=self.model,
            contents=contents,
            config=config,
        )
