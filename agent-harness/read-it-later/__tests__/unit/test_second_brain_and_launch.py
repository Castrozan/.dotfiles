import json
import shlex

import pytest

from hypothesis import given
from hypothesis import strategies as st

from application.session_launch import HerdrSessionLauncher, SessionLaunchFailed
from second_brain.contract import entry_tag_problems, read_contract
from second_brain.entries import entry_file_name, moc_with_link
from second_brain.index import frontmatter_fields, second_brain_index

titles = st.text(min_size=1, max_size=60).filter(
    lambda title: title.strip(" .") and "\n" not in title
)


@given(titles)
def test_an_entry_file_name_never_escapes_the_entry_directory(title):
    file_name = entry_file_name(title)

    assert "/" not in file_name and "\\" not in file_name
    assert file_name.endswith(".md")


def test_a_link_lands_at_the_end_of_by_use_and_a_moc_without_it_gains_the_section():
    moc = "# MOC\n\n## By use\n- [[A]]: a\n\n## Best of\n- [[A]]\n"
    linked = moc_with_link(moc, "- [[B]]: b")

    assert (
        linked == "# MOC\n\n## By use\n- [[A]]: a\n- [[B]]: b\n\n## Best of\n- [[A]]\n"
    )
    assert moc_with_link("# MOC\n", "- [[B]]: b") == "# MOC\n\n## By use\n- [[B]]: b\n"


def test_the_contract_is_read_from_the_vault_at_run_time(sandbox_vault):
    contract = read_contract(sandbox_vault)

    assert "topic/engineering" in contract.tag_values
    assert entry_tag_problems(["topic/engineering"], contract) == []
    assert (
        len(
            entry_tag_problems(
                ["topic/engineering", "topic/ai-agents", "topic/nope"], contract
            )
        )
        == 2
    )


def test_the_index_lists_mocs_and_entries_with_their_theme_and_source(sandbox_vault):
    index = second_brain_index(sandbox_vault)

    assert index["mocs"] == ["Engineering MOC"]
    assert index["entries"] == [
        {
            "title": "Existing entry",
            "path": "Inspiration/Existing entry.md",
            "theme": "Engineering MOC",
            "source_url": "https://x.com/someone/status/42",
        }
    ]


def test_frontmatter_lists_and_quoted_scalars_parse():
    fields = frontmatter_fields(
        '---\ntitle: "A: b"\ntags:\n  - topic/x\n  - medium/ui\n---\nbody'
    )

    assert fields == {"title": "A: b", "tags": ["topic/x", "medium/ui"]}


class ScriptedHerdr:
    def __init__(
        self, agents: list[dict], polls_before_working: int | None = 1
    ) -> None:
        self.agents = agents
        self.polls_before_working = polls_before_working
        self.calls: list[tuple[list[str], str | None]] = []

    def agent_listing(self) -> str:
        started = any(arguments[1:3] == ["pane", "run"] for arguments, _ in self.calls)
        polls = sum(arguments[1:3] == ["agent", "list"] for arguments, _ in self.calls)
        working = (
            started
            and self.polls_before_working is not None
            and polls > self.polls_before_working + 1
        )
        detected = [{"pane_id": "w9:p1", "agent_status": "working"}] if working else []
        return json.dumps({"result": {"agents": self.agents + detected}})

    def __call__(self, arguments: list[str], standard_input: str | None = None) -> str:
        self.calls.append((arguments, standard_input))
        command = " ".join(arguments)
        if "agent list" in command:
            return self.agent_listing()
        if "workspace create" in command:
            return json.dumps(
                {
                    "result": {
                        "workspace": {"workspace_id": "w9"},
                        "root_pane": {"pane_id": "w9:p1"},
                    }
                }
            )
        return "/home/lucas" if "printf" in command else ""


def test_a_local_launch_writes_the_brief_starts_claude_and_waits_for_work():
    herdr = ScriptedHerdr(agents=[])
    launcher = HerdrSessionLauncher(
        command_runner=herdr, local_machine_name="chise", sleep=lambda _: None
    )

    assert launcher.launch("chise", "ril-topic", "# brief") == "launched"

    commands = [arguments for arguments, _ in herdr.calls]
    assert [
        "sh",
        "-c",
        'mkdir -p "$(dirname "$1")" && cat > "$1"',
        "sh",
        "/home/lucas/clawde/ril/briefs/ril-topic.md",
    ] in commands
    assert [
        "herdr",
        "pane",
        "run",
        "w9:p1",
        "claude 'Read /home/lucas/clawde/ril/briefs/ril-topic.md and carry it out.'",
    ] in commands
    assert commands[-2] == ["herdr", "agent", "list"]
    assert commands[-1] == ["herdr", "agent", "rename", "w9:p1", "ril-topic"]
    assert "# brief" in [standard_input for _, standard_input in herdr.calls]


def test_a_remote_launch_goes_over_ssh_and_a_running_session_is_not_launched_twice():
    herdr = ScriptedHerdr(agents=[{"name": "ril-topic"}])
    launcher = HerdrSessionLauncher(command_runner=herdr, local_machine_name="chise")

    assert launcher.launch("kira", "ril-topic", "# brief") == "already-running"
    [(arguments, _)] = herdr.calls
    assert arguments[:2] == ["ssh", "kira"]
    assert shlex.split(arguments[2]) == ["herdr", "agent", "list"]


def test_a_session_that_never_starts_working_fails_the_launch_without_a_name():
    herdr = ScriptedHerdr(agents=[], polls_before_working=None)
    launcher = HerdrSessionLauncher(
        command_runner=herdr, local_machine_name="chise", sleep=lambda _: None
    )

    with pytest.raises(SessionLaunchFailed):
        launcher.launch("chise", "ril-topic", "# brief")
    assert not any(
        arguments[1:3] == ["agent", "rename"] for arguments, _ in herdr.calls
    )
