"""
main.py
-------
Entry point. Simple REPL loop for local testing. All actual behavior
comes from the markdown files under /instructions and /tools — this
script just wires up the Agent and talks to stdin/stdout.
"""

from agent import Agent


def main() -> None:
    agent = Agent()
    print("Agent ready. Type 'exit' to quit.\n")

    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if user_input.lower() in {"exit", "quit"}:
            break
        if not user_input:
            continue

        reply = agent.run(user_input)
        print(f"Agent: {reply}\n")


if __name__ == "__main__":
    main()
