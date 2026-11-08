from hypothesis import given
from hypothesis import strategies as st

from capture_queue.capture_content import (
    capture_kind,
    clipped_text,
    is_stub_line,
    lucas_note,
    origin_url,
)

TWEET_STUB = """[[ReadItLater]] [[Tweet]]

# [Screen](https://x.com/Screeendev/status/2113792408076878334)

> I don't think you understand the gravity of this situation.[pic.twitter.com/x](https://t.co/x)
>
> — Screen (@Screeendev) [October 24, 2026](https://x.com/Screeendev/status/2113792408076878334)
"""

YOUTUBE_STUB = """[[ReadItLater]] [[Youtube]]

# [Memes About Chips](https://youtube.com/shorts/MK5VQXW-zUY?is=z5bI9QQZ3-t5FOIp)

<iframe width="560" src="https://www.youtube-nocookie.com/embed/MK5VQXW-zUY"></iframe>
"""

note_lines = st.text(
    alphabet=st.characters(categories=("L", "N", "Zs"), max_codepoint=0x2FFF),
    min_size=1,
    max_size=60,
).filter(lambda line: line.strip() and not is_stub_line(line))


def test_a_bare_stub_carries_no_note_of_lucas():
    assert lucas_note(TWEET_STUB) == ""
    assert lucas_note(YOUTUBE_STUB) == ""


@given(
    st.lists(note_lines, min_size=1, max_size=4),
    st.sampled_from([TWEET_STUB, YOUTUBE_STUB]),
)
def test_every_line_lucas_adds_outside_the_stub_is_his_note(added_lines, stub):
    note = lucas_note(f"{stub}\n" + "\n".join(added_lines))

    assert note.splitlines() == [line.strip() for line in added_lines]


@given(st.lists(note_lines, max_size=3))
def test_a_claim_or_done_marker_never_reads_as_a_note(added_lines):
    body = (
        TWEET_STUB + "\n".join(added_lines) + "\nstatus:: working\nclaimed_by:: chise\n"
    )

    assert "status::" not in lucas_note(body)


def test_the_first_link_is_the_canonical_origin():
    assert (
        origin_url(TWEET_STUB) == "https://x.com/Screeendev/status/2113792408076878334"
    )
    assert (
        origin_url(YOUTUBE_STUB)
        == "https://youtube.com/shorts/MK5VQXW-zUY?is=z5bI9QQZ3-t5FOIp"
    )
    assert origin_url("no link here") is None


def test_a_clipped_page_reports_its_text_instead_of_a_note():
    clipping = "# Flyline\n\nA Bash plugin for modern command line editing.\n"

    assert capture_kind(clipping) == "Clipping"
    assert lucas_note(clipping) == ""
    assert "modern command line editing" in clipped_text(clipping)
    assert clipped_text(TWEET_STUB) == ""
