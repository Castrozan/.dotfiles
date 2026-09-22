import pytest

from human_facing_reply_test_support import template_violations_in_reply


@pytest.mark.parametrize(
    "destination",
    [
        "https://",
        "https://example.com/unrelated",
        "https://github.com/example/repo/pull/18",
        "https://gitlab.example.com/group/repo/-/merge_requests/17",
        "https:///example/repo/pull/17",
    ],
)
def test_artifact_references_need_a_matching_destination(destination):
    assert template_violations_in_reply("PR #17 is ready. " + destination)


@pytest.mark.parametrize(
    "reply",
    [
        "PR #17 is ready: https://github.com/example/repo/pull/17.",
        "[PR #17](https://github.com/example/repo/pull/17) is ready.",
        "PR #17 is ready.\n\n| Review |\n| --- |\n| https://github.com/example/repo/pull/17 |",
        "MR !17 is ready: https://gitlab.example.com/group/repo/-/merge_requests/17",
        "The pull request is ready: https://github.com/example/repo/pull/17",
    ],
)
def test_links_in_prose_and_tables_can_satisfy_artifact_references(reply):
    assert template_violations_in_reply(reply) == []


def test_an_artifact_named_in_a_table_needs_a_link():
    reply = "| Artifact | Status |\n| --- | --- |\n| PR #17 | ready |"

    assert template_violations_in_reply(reply)


def test_each_numbered_artifact_needs_its_own_destination():
    reply = "PR #17 and PR #18 are ready: https://github.com/example/repo/pull/17"

    assert template_violations_in_reply(reply)


def test_a_quoted_url_does_not_link_an_artifact():
    assert template_violations_in_reply(
        'PR #17 is ready. The input included "https://".'
    )
