class TestValidationFailures:
    def test_exits_non_zero_on_bad_type(
        self, isolated_environment, invoke_memory_write
    ):
        _, workspace = isolated_environment
        result = invoke_memory_write(
            workspace,
            type="garbage",
            key="x",
            fact="a sufficiently long fact",
            author="lucas",
        )
        assert result.returncode == 2
        assert "type" in result.stderr.lower()

    def test_exits_non_zero_on_short_fact(
        self, isolated_environment, invoke_memory_write
    ):
        _, workspace = isolated_environment
        result = invoke_memory_write(
            workspace,
            type="user",
            key="x",
            fact="short",
            author="lucas",
        )
        assert result.returncode == 2
        assert "fact" in result.stderr.lower()

    def test_does_not_create_files_on_validation_failure(
        self, isolated_environment, invoke_memory_write, expected_memory_directory
    ):
        fake_home, workspace = isolated_environment
        invoke_memory_write(
            workspace,
            type="garbage",
            key="x",
            fact="a sufficiently long fact",
            author="lucas",
        )
        memory_dir = expected_memory_directory(fake_home, workspace)
        assert not memory_dir.exists()
