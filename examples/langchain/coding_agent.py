"""Placeholder LangChain coding agent.

Replace this with your actual agent implementation.
See the upstream example for a full version:
https://github.com/kubernetes-sigs/agent-sandbox/tree/main/examples/langchain
"""

import sys


def main():
    print("LangChain coding agent starting...", flush=True)
    print("Replace this file with your agent logic.", flush=True)

    # Keep the container alive so the sandbox stays running.
    try:
        while True:
            line = sys.stdin.readline()
            if not line:
                break
            print(f"Received: {line.strip()}", flush=True)
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
