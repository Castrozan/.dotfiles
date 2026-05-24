class TestSymlinkBridge:
    def test_writes_through_harness_symlink_to_canonical_dir(
        self, isolated_environment, invoke_memory_write
    ):
        fake_home, workspace = isolated_environment
        canonical = workspace / "memory"
        canonical.mkdir()
        encoded = str(workspace).replace("/", "-").replace(".", "-")
        harness_project = fake_home / ".claude" / "projects" / encoded
        harness_project.mkdir(parents=True)
        (harness_project / "memory").symlink_to(canonical)

        result = invoke_memory_write(
            workspace,
            type="user",
            key="lucas",
            fact="a fact written through the symlink bridge",
            author="lucas",
        )
        assert result.returncode == 0, result.stderr
        assert (canonical / "user-lucas.md").exists()
        assert (canonical / "MEMORY.md").exists()
