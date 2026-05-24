import memory_write


class TestSlugifyKey:
    def test_keeps_alphanumeric_underscore(self):
        assert memory_write.slugify_key("abc_123") == "abc_123"

    def test_replaces_non_alphanumeric(self):
        assert (
            memory_write.slugify_key("project name with spaces")
            == "project-name-with-spaces"
        )

    def test_strips_leading_trailing_separators(self):
        assert memory_write.slugify_key("--abc--") == "abc"

    def test_lowercases(self):
        assert memory_write.slugify_key("UserName") == "username"

    def test_collapses_consecutive_non_alphanumeric(self):
        assert memory_write.slugify_key("foo!!!bar") == "foo-bar"


class TestTopicFilenameFor:
    def test_combines_type_and_slugged_key(self):
        assert (
            memory_write.topic_filename_for("user", "Lucas Zanoni")
            == "user-lucas-zanoni.md"
        )

    def test_preserves_numeric_discord_id(self):
        assert (
            memory_write.topic_filename_for("user", "284143065877184512")
            == "user-284143065877184512.md"
        )
