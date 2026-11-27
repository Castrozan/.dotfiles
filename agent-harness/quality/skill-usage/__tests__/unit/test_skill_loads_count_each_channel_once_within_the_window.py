import json
from datetime import UTC, datetime, timedelta

from skill_catalogue import InstalledSkill
from skill_load_events import skill_loads
from skill_usage import usage_by_skill

NOW = datetime.now(UTC)
RECENT = (NOW - timedelta(days=1)).isoformat().replace("+00:00", "Z")
STALE = (NOW - timedelta(days=40)).isoformat().replace("+00:00", "Z")


def assistant_tool_use(record_type, identifier, name, tool_input, timestamp=RECENT):
    return {
        "type": record_type,
        "sessionId": "main-session",
        "timestamp": timestamp,
        "message": {
            "role": "assistant",
            "content": [
                {
                    "type": "tool_use",
                    "id": identifier,
                    "name": name,
                    "input": tool_input,
                }
            ],
        },
    }


def user_text(text, session="main-session"):
    return {
        "type": "user",
        "sessionId": session,
        "timestamp": RECENT,
        "message": {"role": "user", "content": [{"type": "text", "text": text}]},
    }


def write_transcript(path, records):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(json.dumps(record, separators=(",", ":")) for record in records)
        + "\n"
    )


def test_skill_loads_count_each_channel_once_within_the_window(tmp_path):
    projects = tmp_path / "projects"
    write_transcript(
        projects / "repository" / "main-session.jsonl",
        [
            assistant_tool_use(
                "assistant", "toolu_1", "Skill", {"skill": "dotfiles:coding"}
            ),
            assistant_tool_use(
                "api-request-blob", "toolu_1", "Skill", {"skill": "dotfiles:coding"}
            ),
            assistant_tool_use("assistant", "toolu_2", "Skill", {"skill": "nix"}),
            assistant_tool_use(
                "assistant", "toolu_3", "Skill", {"skill": "other-plugin:coding"}
            ),
            assistant_tool_use(
                "assistant",
                "toolu_4",
                "Skill",
                {"skill": "dotfiles:coding"},
                timestamp=STALE,
            ),
            assistant_tool_use(
                "assistant",
                "toolu_5",
                "Read",
                {"file_path": "/plugin/library/skills/ril/SKILL.md"},
            ),
            assistant_tool_use(
                "assistant",
                "toolu_6",
                "Read",
                {"file_path": "/plugin/library/skills/ril/knowledge.md"},
            ),
            user_text(
                "<command-message>review</command-message>\n<command-name>/dotfiles:review</command-name>"
            ),
            user_text("<command-name>/compact</command-name>"),
        ],
    )
    write_transcript(
        projects / "repository" / "main-session" / "subagents" / "agent-1.jsonl",
        [
            user_text(
                "<command-name>coding</command-name>\n<skill-format>true</skill-format>"
            )
        ],
    )
    catalogue = {
        name: InstalledSkill(name, "top", 1)
        for name in ("coding", "nix", "ril", "review")
    }

    usage = usage_by_skill(skill_loads(projects, NOW - timedelta(days=30)), catalogue)

    assert {name: dict(skill.loads_by_channel) for name, skill in usage.items()} == {
        "coding": {"agent": 1, "pinned": 1},
        "nix": {"agent": 1},
        "ril": {"nested": 1},
        "review": {"typed": 1},
    }
