"""
AI Coding Agent - powered by Groq (OpenAI-compatible API)

This agent explores a target repository, plans changes based on a user
request, and applies those changes using simple file tools.
"""

import os
import json
import time
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise RuntimeError("GROQ_API_KEY not found in environment (.env file)")

client = OpenAI(
    api_key=GROQ_API_KEY,
    base_url="https://api.groq.com/openai/v1",
)

MODEL = "llama-3.3-70b-versatile"

TARGET_REPO = Path(__file__).parent / "target-repo"
USER_REQUEST = "Add a way for users to filter/organise their notes by tag, for example a GET endpoint that returns all notes matching a given tag."

MAX_TURNS = 25
RETRY_WAIT_SECONDS = 8
MAX_RETRIES = 5

# ---------------------------------------------------------------------------
# Tool implementations (operate on TARGET_REPO)
# ---------------------------------------------------------------------------

def list_files(_args=None):
    files = []
    for p in TARGET_REPO.rglob("*"):
        if p.is_file() and "node_modules" not in p.parts and ".git" not in p.parts:
            files.append(str(p.relative_to(TARGET_REPO)))
    return {"files": files}


def read_file(args):
    path = TARGET_REPO / args["path"]
    if not path.exists():
        return {"error": f"File not found: {args['path']}"}
    return {"content": path.read_text(encoding="utf-8", errors="replace")}


def write_file(args):
    path = TARGET_REPO / args["path"]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(args["content"], encoding="utf-8")
    return {"status": "written", "path": args["path"]}


TOOL_IMPLEMENTATIONS = {
    "list_files": list_files,
    "read_file": read_file,
    "write_file": write_file,
}

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "list_files",
            "description": "List all files in the target repository (relative paths).",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read the contents of a file in the target repository.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Relative path to the file"}
                },
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Write (create or overwrite) a file in the target repository.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Relative path to the file"},
                    "content": {"type": "string", "description": "Full new content of the file"},
                },
                "required": ["path", "content"],
            },
        },
    },
]

SYSTEM_PROMPT = f"""You are an AI coding agent. You have access to a target repository at
'{TARGET_REPO}' via tools (list_files, read_file, write_file).

Your job:
1. Explore the repository using list_files and read_file to understand its structure.
2. Create a brief execution plan for implementing the user's request.
3. Actually apply the changes using write_file calls (do not just describe them).
4. Preserve all existing functionality while adding the new feature.
5. When you are completely done applying all changes, respond with a final
   message that starts with the literal word 'SUMMARY:' followed by a concise
   summary of the changes you made. Do not write 'SUMMARY:' until you have
   actually made all the write_file calls needed.

Be efficient: don't re-read files you've already read. Don't just describe a
plan and stop -- you must call write_file to actually implement it before
giving your SUMMARY.
"""


def send_with_retry(messages, tools):
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            return client.chat.completions.create(
                model=MODEL,
                messages=messages,
                tools=tools,
                tool_choice="auto",
            )
        except Exception as e:
            msg = str(e)
            if "rate" in msg.lower() or "429" in msg:
                print(f"  [rate limited, attempt {attempt}/{MAX_RETRIES}, waiting {RETRY_WAIT_SECONDS}s...]")
                time.sleep(RETRY_WAIT_SECONDS)
                continue
            if "tool_use_failed" in msg or "Failed to call a function" in msg:
                print(f"  [model produced a malformed tool call, attempt {attempt}/{MAX_RETRIES}, retrying...]")
                messages.append(
                    {
                        "role": "user",
                        "content": (
                            "Your last tool call was malformed JSON and could not be "
                            "processed. Please retry the tool call with strictly valid "
                            "JSON arguments. Use forward slashes (/) in file paths, not "
                            "backslashes."
                        ),
                    }
                )
                time.sleep(2)
                continue
            raise
    raise RuntimeError("Max retries exceeded.")


def run_agent():
    print(f"Target repo: {TARGET_REPO}")
    print(f"User request: {USER_REQUEST}\n")

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": USER_REQUEST},
    ]

    tool_call_log = []

    for turn in range(1, MAX_TURNS + 1):
        response = send_with_retry(messages, TOOLS)
        choice = response.choices[0]
        msg = choice.message

        # If the model wants to call tools
        if msg.tool_calls:
            messages.append(
                {
                    "role": "assistant",
                    "content": msg.content or "",
                    "tool_calls": [
                        {
                            "id": tc.id,
                            "type": "function",
                            "function": {
                                "name": tc.function.name,
                                "arguments": tc.function.arguments,
                            },
                        }
                        for tc in msg.tool_calls
                    ],
                }
            )

            for tc in msg.tool_calls:
                name = tc.function.name
                try:
                    args = json.loads(tc.function.arguments) if tc.function.arguments else {}
                except json.JSONDecodeError:
                    args = {}

                print(f"  [tool call] {name}({args})")
                tool_call_log.append(f"{name}({args})")

                impl = TOOL_IMPLEMENTATIONS.get(name)
                result = impl(args) if impl else {"error": f"Unknown tool {name}"}

                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "content": json.dumps(result),
                    }
                )
            continue

        # No tool calls -- this is a text response
        content = msg.content or ""
        messages.append({"role": "assistant", "content": content})

        if "SUMMARY:" in content:
            print("\n=== AGENT FINAL RESPONSE ===")
            print(content)
            print("\n=== TOOL CALL LOG ===")
            for entry in tool_call_log:
                print(f"- {entry}")
            return

        # Model gave a plan/commentary but didn't finish -- nudge it forward
        print("\n[agent paused without SUMMARY -- nudging it to continue]\n")
        messages.append(
            {
                "role": "user",
                "content": (
                    "Please continue. If you have described a plan, now actually "
                    "apply it using write_file calls. Only respond with 'SUMMARY:' "
                    "once all changes have been written to disk."
                ),
            }
        )

    print("\n[Stopped: reached MAX_TURNS without a final SUMMARY]")
    print("=== TOOL CALL LOG ===")
    for entry in tool_call_log:
        print(f"- {entry}")


if __name__ == "__main__":
    run_agent()