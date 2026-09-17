# AI Agent Skeleton (MVP — logic in markdown)

Single agent, multiple skills, multiple tools. All business logic
lives in `.md` files; Python is orchestration only.

## Structure

```
ai-agent-skeleton/
├── agent/                      # Python engine — no business logic
│   ├── __init__.py
│   ├── config.py                 # loads all .md files
│   ├── core.py                   # Agent class: message loop, tool dispatch
│   ├── llm.py                    # thin Google Gemini (google-genai) wrapper
│   ├── sql_agent.py              # LangChain PostgreSQL SQL agent
│   └── tools.py                  # tool registry (schema + implementation)
│
├── instructions/
│   ├── system_prompt.md          # agent purpose & scope     <- logic
│   ├── persona.md                # tone & voice               <- logic
│   ├── rules.md                  # hard constraints            <- logic
│   └── skills/                   # capabilities the agent has
│       ├── math_and_lookup.md    # <- logic
│       └── summarization.md      # <- logic
│
├── tools/
│   ├── search.md                 # tool description for the LLM <- logic
│   └── calculator.md             # tool description for the LLM <- logic
│   └── ask_database.md            # PostgreSQL query tool
│
├── main.py                     # REPL entry point
├── requirements.txt
├── .env.example
└── README.md
```

## Principle

- **Python** (`agent/`) = mechanics only: load files, call the Gemini
  API, run the loop, dispatch tool calls.
- **Markdown** (`instructions/`) = everything that defines what the
  agent actually does: purpose, persona, rules, skills, tool
  descriptions.

To change agent behavior, edit `.md` files — not Python.

## Skills vs tools

- A **skill** (`instructions/skills/*.md`) is knowledge/instructions
  for *how to handle a kind of request* — no code involved. Every
  skill is loaded into the system prompt automatically.
- A **tool** (`tools/*.md` + an entry in `agent/tools.py`) is an
  actual function the agent can call (search, calculator, an API,
  etc.). A tool needs both halves — the `.md` doc (what the LLM sees)
  and a Python implementation — to be usable.

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env   # fill in both API and PostgreSQL settings
python main.py
```

Get a `GOOGLE_API_KEY` from [Google AI Studio](https://aistudio.google.com/apikey).

Set `POSTGRES_DATABASE_URL` to a SQLAlchemy PostgreSQL URL, for example:

```text
postgresql+psycopg://user:password@localhost:5432/database_name
```

Questions about the database are routed to the LangChain SQL agent through the
`ask_database` tool. The SQL agent is configured for read-only queries and is
created lazily on the first database question.

## Adding a skill

Add a new file under `instructions/skills/`. It's picked up
automatically — no code change needed.

## Adding a tool

1. Write `tools/<name>.md` — what it does, when to call it.
2. Add a Python function + JSON schema to `IMPLEMENTATIONS` in
   `agent/tools.py`. Schemas are plain JSON-schema dicts (`type`,
   `properties`, `required`) — `agent/tools.py` wraps them into
   Gemini's `FunctionDeclaration`/`Tool` objects for you.

## Note on the MVP scope

- All skills are always loaded into the system prompt (simplest thing
  that works). If the skill set grows large enough to bloat the
  prompt or cause skill collisions, the next step is *selecting*
  relevant skills per request rather than loading all of them — but
  that selection logic is itself a business decision, so keep the
  criteria for choosing a skill in markdown (e.g. an index/router
  skill file) rather than hardcoding it in Python.
- `calculator`'s implementation uses `eval()` as a stub — swap for a
  safe expression parser before using this beyond local testing.
- `search`'s implementation is a stub returning a placeholder string —
  wire it up to a real search API/tool call.
