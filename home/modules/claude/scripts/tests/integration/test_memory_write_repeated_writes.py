class TestRepeatedWrites:
    def test_appends_new_entries_to_existing_topic(
        self, isolated_environment, invoke_memory_write, expected_memory_directory
    ):
        fake_home, workspace = isolated_environment
        invoke_memory_write(
            workspace,
            type="user",
            key="lucas",
            fact="lucas uses pnpm not npm for js",
            author="lucas",
        )
        invoke_memory_write(
            workspace,
            type="user",
            key="lucas",
            fact="lucas uses fish shell on macbook",
            author="lucas",
        )
        memory_dir = expected_memory_directory(fake_home, workspace)
        topic_lines = [
            line
            for line in (memory_dir / "user-lucas.md").read_text().splitlines()
            if line.startswith("- ")
        ]
        assert len(topic_lines) == 2

    def test_skips_duplicate_fact(
        self, isolated_environment, invoke_memory_write, expected_memory_directory
    ):
        fake_home, workspace = isolated_environment
        kw = dict(
            type="user",
            key="lucas",
            fact="lucas uses pnpm not npm",
            author="lucas",
        )
        first = invoke_memory_write(workspace, **kw)
        second = invoke_memory_write(workspace, **kw)
        assert first.returncode == 0
        assert second.returncode == 0
        assert "skipped" in second.stderr.lower()
        memory_dir = expected_memory_directory(fake_home, workspace)
        topic_lines = [
            line
            for line in (memory_dir / "user-lucas.md").read_text().splitlines()
            if line.startswith("- ")
        ]
        assert len(topic_lines) == 1

    def test_index_pointer_upserts_in_place(
        self, isolated_environment, invoke_memory_write, expected_memory_directory
    ):
        fake_home, workspace = isolated_environment
        invoke_memory_write(
            workspace,
            type="user",
            key="lucas",
            fact="first durable fact about lucas",
            author="lucas",
        )
        invoke_memory_write(
            workspace,
            type="user",
            key="lucas",
            fact="second durable fact about lucas",
            author="lucas",
        )
        memory_dir = expected_memory_directory(fake_home, workspace)
        index_pointer_lines = [
            line
            for line in (memory_dir / "MEMORY.md").read_text().splitlines()
            if line.startswith("- [user/lucas]")
        ]
        assert len(index_pointer_lines) == 1
        assert "second durable fact" in index_pointer_lines[0]
