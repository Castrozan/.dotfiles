from datetime import date

import pytest

from append_agent_memory_fact import (
    INDEX_FILE_NAME,
    MemoryWriteRefused,
    append_agent_memory_fact,
)

WRITTEN_ON = date(2026, 8, 8)


@pytest.fixture
def agent_workspace(tmp_path, monkeypatch):
    agents_directory = tmp_path / "clawde"
    workspace = agents_directory / "monster"
    workspace.mkdir(parents=True)
    monkeypatch.setenv("CLAWDE_AGENTS_DIRECTORY", str(agents_directory))
    return workspace


def append(workspace, **overrides):
    arguments = {
        "topic_type": "project",
        "topic_key": "guild-lingo",
        "fact": "gato a jato is the guild name for the Managarmr",
        "author": "monster",
        "written_on": WRITTEN_ON,
    }
    arguments.update(overrides)
    return append_agent_memory_fact(workspace, **arguments)


def test_a_first_fact_creates_the_topic_file_with_a_heading(agent_workspace):
    topic_file = append(agent_workspace)

    assert topic_file.read_text(encoding="utf-8") == (
        "# project-guild-lingo\n"
        "\n"
        "- 2026-08-08 (monster): gato a jato is the guild name for the Managarmr\n"
    )


def test_a_second_fact_appends_below_the_first(agent_workspace):
    append(agent_workspace)
    topic_file = append(agent_workspace, fact="detetive maconha is Yofukashi no Uta")

    assert topic_file.read_text(encoding="utf-8").splitlines()[-2:] == [
        "- 2026-08-08 (monster): gato a jato is the guild name for the Managarmr",
        "- 2026-08-08 (monster): detetive maconha is Yofukashi no Uta",
    ]


def test_the_index_carries_the_newest_fact_of_every_topic(agent_workspace):
    append(agent_workspace)
    append(agent_workspace, fact="the newest one wins the index line")
    append(
        agent_workspace,
        topic_type="user",
        topic_key="640610166458417162",
        fact="xamitos",
    )

    index = (agent_workspace / "memory" / INDEX_FILE_NAME).read_text(encoding="utf-8")

    assert (
        "- [project/guild-lingo](project-guild-lingo.md): 2026-08-08 (monster): the newest one wins the index line\n"
        in index
    )
    assert (
        "- [user/640610166458417162](user-640610166458417162.md): 2026-08-08 (monster): xamitos\n"
        in index
    )
    assert "gato a jato" not in index


def test_a_rewritten_index_drops_an_entry_whose_topic_file_is_gone(agent_workspace):
    append(agent_workspace)
    (agent_workspace / "memory" / "project-guild-lingo.md").unlink()
    append(
        agent_workspace,
        topic_type="reference",
        topic_key="guild-channels",
        fact="general",
    )

    index = (agent_workspace / "memory" / INDEX_FILE_NAME).read_text(encoding="utf-8")

    assert "guild-lingo" not in index
    assert "guild-channels" in index


def test_a_multiline_fact_is_flattened_so_one_fact_stays_one_line(agent_workspace):
    topic_file = append(agent_workspace, fact="first line\nsecond   line\n")

    assert topic_file.read_text(encoding="utf-8").splitlines()[-1] == (
        "- 2026-08-08 (monster): first line second line"
    )


def test_an_empty_fact_is_refused(agent_workspace):
    with pytest.raises(MemoryWriteRefused):
        append(agent_workspace, fact="   \n  ")


@pytest.mark.parametrize(
    "topic_key", ["../../../etc/passwd", "has space", "UPPER", "", "a/b"]
)
def test_a_topic_key_that_could_escape_the_memory_directory_is_refused(
    agent_workspace, topic_key
):
    with pytest.raises(MemoryWriteRefused):
        append(agent_workspace, topic_key=topic_key)


def test_an_author_carrying_markup_is_refused(agent_workspace):
    with pytest.raises(MemoryWriteRefused):
        append(agent_workspace, author="monster](../../../etc/passwd)")


def test_a_working_directory_outside_the_agents_directory_is_refused(
    agent_workspace, tmp_path
):
    with pytest.raises(MemoryWriteRefused):
        append(tmp_path / "somewhere-else")


def test_a_nested_directory_inside_an_agent_workspace_is_refused(agent_workspace):
    nested = agent_workspace / "memory"
    nested.mkdir(parents=True, exist_ok=True)

    with pytest.raises(MemoryWriteRefused):
        append(nested)
