class TestSeparateTopicsCoexist:
    def test_distinct_types_create_distinct_files(
        self, isolated_environment, invoke_memory_write, expected_memory_directory
    ):
        fake_home, workspace = isolated_environment
        invoke_memory_write(
            workspace,
            type="user",
            key="lucas",
            fact="lucas uses fish shell on macbook",
            author="lucas",
        )
        invoke_memory_write(
            workspace,
            type="feedback",
            key="never-mock-database",
            fact="integration tests must hit real database, not mocks",
            author="lucas",
        )
        memory_dir = expected_memory_directory(fake_home, workspace)
        assert (memory_dir / "user-lucas.md").exists()
        assert (memory_dir / "feedback-never-mock-database.md").exists()
        index_text = (memory_dir / "MEMORY.md").read_text()
        assert "[user/lucas]" in index_text
        assert "[feedback/never-mock-database]" in index_text
