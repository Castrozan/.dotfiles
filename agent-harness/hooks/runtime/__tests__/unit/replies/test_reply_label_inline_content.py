import pytest

from human_facing_reply_test_support import (
    labeled_reply_of,
    template_violations_in_reply,
)


@pytest.mark.parametrize("label", ["What is this session about?", "Done", "Next"])
@pytest.mark.parametrize("markup", ["{}:", "**{}:**", "__{}:__", "**{}**:", "**{}:"])
@pytest.mark.parametrize("separator", ["\n", "\r\n", "\r", "\n\n", "  \n", "\\\n"])
def test_label_content_cannot_start_on_the_next_line(label, markup, separator):
    reply = markup.format(label) + separator + "The check passed."

    violations = template_violations_in_reply(reply)

    assert any("same line" in violation for violation in violations)


@pytest.mark.parametrize("separator", ["\n", "\n\n", "<br>", "<BR />"])
def test_long_reply_requires_inline_label_content(separator):
    reply = labeled_reply_of(90).replace("**done:** ", "**done:**" + separator)

    assert any(
        "same line" in violation for violation in template_violations_in_reply(reply)
    )


@pytest.mark.parametrize(
    "suffix", ["", " ", "  ", "\\\n", "\n| Result |\n| --- |\n| Passed |"]
)
def test_empty_label_lines_require_inline_content(suffix):
    assert template_violations_in_reply("**Done:**" + suffix)


@pytest.mark.parametrize(
    "content",
    [
        "The check passed.",
        "**The check passed.**",
        "`verified`",
        "[proof](https://example.org/result)",
        "![proof](https://example.org/result.png)",
        "![](https://example.org/result.png)",
        "The check\npassed.",
        "The check passed.<br>More detail.",
    ],
)
def test_inline_content_and_later_continuations_are_allowed(content):
    assert template_violations_in_reply("**Done:** " + content) == []


@pytest.mark.parametrize(
    "example",
    [
        "```text\nDone:\nThe check passed.\n```",
        "> **Done:**\n> The check passed.",
        "| Format |\n| --- |\n| Done: |\n| The check passed. |",
        "The example is `Done:` followed by a newline.",
    ],
)
def test_quoted_and_visual_examples_are_not_response_labels(example):
    assert template_violations_in_reply(example) == []
