"""UserPromptSubmit hook: emits the workflow reminder unless bypass permissions is active."""

from __future__ import annotations

import json
import sys

REMINDER = (
    "[workflow] 1) ask questions 2) /research 3) /plan 4) plan-reviewer agent "
    "5) user approval 6) implement 7) implementation-verifier agent. "
    "Do NOT skip steps. Do NOT write code before plan is approved."
)


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        payload = {}

    if payload.get("permission_mode") == "bypassPermissions":
        return 0

    print(REMINDER)
    return 0


if __name__ == "__main__":
    sys.exit(main())
