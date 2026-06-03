# .agent/hooks/pre_tool_use.py
import json
import sys

payload = json.load(sys.stdin)

tool_call = payload.get("toolCall", {})
tool_name = tool_call.get("name", "")
args = tool_call.get("args", {})

command_line = args.get("CommandLine", "")

dangerous_patterns = [
    "rm -rf",
    "del /s",
    "format ",
    "git push --force",
    "curl ",
    "wget ",
]

if tool_name == "run_command":
    for pattern in dangerous_patterns:
        if pattern.lower() in command_line.lower():
            print(json.dumps({
                "decision": "force_ask",
                "reason": f"Command contains risky pattern: {pattern}"
            }))
            sys.exit(0)

print(json.dumps({
    "decision": "allow"
}))