import time

from human_facing_reply_test_support import template_violations_in_reply


def test_unmatched_curly_quotes_have_bounded_validation_time():
    template_violations_in_reply("The check is ready.")
    reply = "“" * 16000 + " unquoted — result"
    started = time.perf_counter()

    violations = template_violations_in_reply(reply)

    elapsed = time.perf_counter() - started
    assert any("em dash" in violation for violation in violations)
    assert elapsed < 0.5
