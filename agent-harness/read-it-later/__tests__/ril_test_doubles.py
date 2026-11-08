from datetime import datetime, timezone
from pathlib import Path

CONTRIBUTING = """# Contributing to the Second Brain

Entries also carry: `title`, `source-url`. See `templates/Inspiration Entry.md`.
Tag only from the [[Tag Legend]].
"""

ENTRY_TEMPLATE = """---
title: "{{title}}"
type: inspiration
status: inbox
source-url:
creator:
platform:
captured: {{date:YYYY-MM-DD}}
rating:
license: reference-only
palette: []
tags:
  - topic/design
---

![[paste-image-here.png|400]]

## Why it resonates
> One or two lines on what makes this work.

## What to steal
-

## Reuse for
[[Design & Digital Art MOC]]:
"""

TAG_LEGEND = """# Tag Legend

- `#topic/engineering`
- `#topic/ai-agents`
- `#medium/ui`
"""

ENGINEERING_MOC = """---
type: moc
---
# Engineering MOC

Up: [[Learning MOC]]

## By use
- [[Existing entry]]: already here

## Best of
- [[Existing entry]]
"""

EXISTING_ENTRY = """---
title: "Existing entry"
source-url: https://x.com/someone/status/42
tags:
  - topic/engineering
---
Up: [[Engineering MOC]]
"""


def write_sandbox_vault(vault: Path) -> Path:
    second_brain = vault / "Second Brain"
    files = {
        second_brain / "CONTRIBUTING.md": CONTRIBUTING,
        second_brain / "templates" / "Inspiration Entry.md": ENTRY_TEMPLATE,
        second_brain / "Atlas" / "Tag Legend.md": TAG_LEGEND,
        second_brain / "Atlas" / "Engineering MOC.md": ENGINEERING_MOC,
        second_brain / "Inspiration" / "Existing entry.md": EXISTING_ENTRY,
    }
    for path, text in files.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    (vault / "ReadItLater Inbox").mkdir(parents=True, exist_ok=True)
    return vault


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class RecordingForge:
    def __init__(self) -> None:
        self.pull_requests: dict[int, dict] = {}
        self.closed: list[dict] = []
        self.next_comment_id = 1
        self.merge_failure: Exception | None = None

    def open_pull_requests(self, branch_prefix: str) -> list[dict]:
        return [
            pull_request
            for pull_request in self.pull_requests.values()
            if pull_request["state"] == "OPEN"
            and pull_request["headRefName"].startswith(branch_prefix)
        ]

    def closed_pull_requests(self, branch_prefix: str) -> list[dict]:
        return self.closed

    def pull_request(self, number: int) -> dict:
        return self.pull_requests[number]

    def open_pull_request(self, branch: str, title: str, body: str) -> dict:
        number = len(self.pull_requests) + 1
        url = f"https://forge.example/pull/{number}"
        self.pull_requests[number] = {
            "number": number,
            "headRefName": branch,
            "state": "OPEN",
            "title": title,
            "body": body,
            "url": url,
            "comments": [],
        }
        return {"number": number, "url": url}

    def comment(self, number: int, body: str, created_at: str | None = None) -> str:
        comment_id = f"comment-{self.next_comment_id}"
        self.next_comment_id += 1
        self.pull_requests[number]["comments"].append(
            {"id": comment_id, "body": body, "createdAt": created_at or utc_now()}
        )
        return comment_id

    def replace_body(self, number: int, body: str) -> None:
        self.pull_requests[number]["body"] = body

    def merge(self, number: int) -> None:
        if self.merge_failure:
            raise self.merge_failure
        self.pull_requests[number]["state"] = "MERGED"


class RecordingLauncher:
    def __init__(self) -> None:
        self.launches: list[tuple[str, str, str]] = []

    def launch(self, host: str, session_name: str, brief_text: str) -> str:
        self.launches.append((host, session_name, brief_text))
        return "launched"
