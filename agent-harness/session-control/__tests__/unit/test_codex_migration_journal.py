from agent_session import codex_launcher_migration as migration


def test_separate_attempts_retain_both_results(prepared_migration):
    plan, commands, directory, clock = prepared_migration
    migration.migrate(plan, commands, directory / "first")
    first = (directory / "first/result.json").read_bytes()
    migration.migrate(plan, commands, directory / "second")
    assert (directory / "first/result.json").read_bytes() == first
    assert (directory / "first/old-processes.json").exists()
    assert (directory / "second/old-processes.json").exists()
