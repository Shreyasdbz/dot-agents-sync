"""Conservative guard for explicit credential paths; not a shell sandbox."""

import json
import re
import sys


def decision(payload):
    tool_input = payload.get("tool_input", payload)
    text = json.dumps(tool_input, ensure_ascii=False)
    patterns = [
        r"(?:^|[/\\\s\"'])\.env(?:[.\"'\s/\\]|$)",
        r"\.ssh[/\\]",
        r"\.aws[/\\]credentials",
        r"(?:id_rsa|id_ed25519)(?:[.\"'\s]|$)",
    ]
    return any(re.search(pattern, text) for pattern in patterns)


def main():
    try:
        data = sys.stdin.buffer.read(1024 * 1024 + 1)
        if len(data) > 1024 * 1024:
            return 2
        payload = json.loads(data)
        if not isinstance(payload, dict):
            return 2
        if decision(payload):
            print("Credential-path access requires a separately reviewed action.", file=sys.stderr)
            return 2
        return 0
    except (ValueError, TypeError):
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
