import argparse

import pytest

import memory_write


class TestValidateArguments:
    def make_arguments(self, **overrides):
        defaults = {
            "type": "user",
            "key": "lucas",
            "fact": "a sufficiently long fact about lucas preferences",
            "author": "lucas",
            "source_msg": None,
        }
        defaults.update(overrides)
        return argparse.Namespace(**defaults)

    def test_accepts_valid_arguments(self):
        memory_write.validate_arguments(self.make_arguments())

    def test_rejects_unknown_type(self):
        with pytest.raises(SystemExit):
            memory_write.validate_arguments(self.make_arguments(type="bogus"))

    def test_rejects_too_short_fact(self):
        with pytest.raises(SystemExit):
            memory_write.validate_arguments(self.make_arguments(fact="short"))

    def test_rejects_too_long_fact(self):
        with pytest.raises(SystemExit):
            memory_write.validate_arguments(
                self.make_arguments(fact="x" * (memory_write.MAXIMUM_FACT_LENGTH + 1))
            )

    def test_rejects_empty_key(self):
        with pytest.raises(SystemExit):
            memory_write.validate_arguments(self.make_arguments(key=""))

    def test_rejects_whitespace_only_key(self):
        with pytest.raises(SystemExit):
            memory_write.validate_arguments(self.make_arguments(key="   "))

    def test_rejects_empty_author(self):
        with pytest.raises(SystemExit):
            memory_write.validate_arguments(self.make_arguments(author=""))
