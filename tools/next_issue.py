"""Select the single highest-priority open GitHub issue for Codex work.

Requires GitHub CLI (`gh`) to be installed and authenticated.
The script deliberately performs deterministic summarization so selecting work does not
consume LLM context before Codex starts the actual task.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

REPO = "tomiya7688/kadoka_code_atlas"
OUTPUT = Path(".codex") / "next_issue.md"

# Lower number wins. Both common P-labels and readable labels are supported.
PRIORITY_LABELS = {
    "p0": 0,
    "priority:p0": 0,
    "priority:critical": 0,
    "critical": 0,
    "p1": 1,
    "priority:p1": 1,
    "priority:high": 1,
    "high priority": 1,
    "p2": 2,
    "priority:p2": 2,
    "priority:medium": 2,
    "medium priority": 2,
    "p3": 3,
    "priority:p3": 3,
    "priority:low": 3,
    "low priority": 3,
}


def run_gh() -> list[dict]:
    command = [
        "gh", "issue", "list",
        "--repo", REPO,
        "--state", "open",
        "--limit", "100",
        "--json", "number,title,body,labels,url,updatedAt",
    ]
    try:
        completed = subprocess.run(
            command,
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
    except FileNotFoundError:
        sys.exit("ERROR: GitHub CLI (gh) was not found. Install it and run `gh auth login`.")
    except subprocess.CalledProcessError as exc:
        detail = (exc.stderr or exc.stdout or "gh failed").strip()
        sys.exit(f"ERROR: Could not read GitHub issues: {detail}")
    return json.loads(completed.stdout)


def priority(issue: dict) -> tuple[int, int]:
    labels = {
        label.get("name", "").strip().lower()
        for label in issue.get("labels", [])
    }
    rank = min((PRIORITY_LABELS[name] for name in labels if name in PRIORITY_LABELS), default=50)

    # Within the same priority, older issue number wins. This keeps ordering stable and
    # avoids silently changing priorities based on wording or LLM interpretation.
    return rank, int(issue["number"])


def compact_body(body: str, max_chars: int = 900) -> str:
    if not body:
        return "No description provided."

    lines: list[str] = []
    in_code_block = False
    for raw in body.splitlines():
        line = raw.strip()
        if line.startswith("```"):
            in_code_block = not in_code_block
            continue
        if in_code_block or not line:
            continue
        # Remove common Markdown decoration while preserving useful wording.
        line = re.sub(r"^#{1,6}\s*", "", line)
        line = re.sub(r"^[-*+]\s+", "", line)
        line = re.sub(r"^\d+[.)]\s+", "", line)
        line = re.sub(r"\[(.*?)\]\([^)]*\)", r"\1", line)
        if line.lower().startswith(("<!--", "template:")):
            continue
        lines.append(line)

    summary = " ".join(lines)
    summary = re.sub(r"\s+", " ", summary).strip()
    if not summary:
        return "No usable description provided."
    if len(summary) > max_chars:
        return summary[: max_chars - 1].rstrip() + "…"
    return summary


def main() -> int:
    issues = run_gh()
    if not issues:
        print("No open issues.")
        return 0

    issue = min(issues, key=priority)
    label_names = [label.get("name", "") for label in issue.get("labels", [])]
    rank, _ = priority(issue)
    priority_text = f"P{rank}" if rank < 4 else "unlabeled"
    summary = compact_body(issue.get("body") or "")

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(
        "\n".join(
            [
                "# Next Issue",
                "",
                f"Issue: #{issue['number']} — {issue['title']}",
                f"Priority: {priority_text}",
                f"Labels: {', '.join(label_names) if label_names else '(none)'}",
                f"URL: {issue['url']}",
                "",
                "## Compact summary",
                summary,
                "",
                "## Codex instruction",
                "Implement or resolve this issue as the current highest-priority task.",
                "Read AGENTS.md first, then only the docs/specs files relevant to this issue.",
                "Do not load unrelated specifications. Inspect the existing implementation before changing it.",
                "Keep changes scoped to this issue and run the relevant checks after editing.",
                "",
            ]
        ),
        encoding="utf-8",
    )

    print(f"[{priority_text}] #{issue['number']} {issue['title']}")
    print(summary)
    print(f"\nCodex context written to: {OUTPUT}")
    print(issue["url"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
