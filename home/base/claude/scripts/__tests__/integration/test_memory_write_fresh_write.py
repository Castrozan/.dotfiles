class TestFreshWrite:
    def test_creates_topic_file_with_dated_entry(
        self, isolated_environment, invoke_memory_write, expected_memory_directory
    ):
        fake_home, workspace = isolated_environment
        result = invoke_memory_write(
            workspace,
            type="user",
            key="123456789012345678",
            fact="lucas prefers pnpm over npm for js projects",
            author="lucas",
        )
        assert result.returncode == 0, result.stderr
        memory_dir = expected_memory_directory(fake_home, workspace)
        topic_path = memory_dir / "user-123456789012345678.md"
        assert topic_path.exists()
        content = topic_path.read_text()
        assert "lucas prefers pnpm over npm" in content
        assert "(lucas):" in content

    def test_creates_seeded_index(
        self, isolated_environment, invoke_memory_write, expected_memory_directory
    ):
        fake_home, workspace = isolated_environment
        result = invoke_memory_write(
            workspace,
            type="user",
            key="lucas",
            fact="a sufficiently long fact about lucas",
            author="lucas",
        )
        assert result.returncode == 0, result.stderr
        memory_dir = expected_memory_directory(fake_home, workspace)
        index = (memory_dir / "MEMORY.md").read_text()
        assert "# Memory index" in index
        assert "[user/lucas](user-lucas.md)" in index
