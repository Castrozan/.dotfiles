import subprocess
from pathlib import Path

PI_MODULE_DIRECTORY = Path(__file__).resolve().parents[2]
LAUNCHER_SCRIPT_PATH = (
    PI_MODULE_DIRECTORY / "scripts" / "launch-pi-with-the-interactive-reply-rules.sh"
)


def build_argv_recorder(directory: Path) -> tuple[Path, Path]:
    recorded_argv = directory / "recorded-argv"
    recorder = directory / "pi-recorder"
    recorder.write_text(
        f'#!/usr/bin/env bash\nprintf "%s\\n" "$@" > "{recorded_argv}"\nexit 0\n'
    )
    recorder.chmod(0o755)
    return recorder, recorded_argv


def run_launcher(tmp_path: Path, *arguments: str) -> list[str]:
    recorder, recorded_argv = build_argv_recorder(tmp_path)
    reply_rules_file = tmp_path / "interactive-reply-rules.md"
    reply_rules_file.write_text("reply rules\n")

    completed = subprocess.run(
        ["bash", str(LAUNCHER_SCRIPT_PATH), *arguments],
        env={
            "PATH": "/usr/bin:/bin",
            "PI_UNWRAPPED_BINARY": str(recorder),
            "PI_INTERACTIVE_REPLY_RULES_FILE": str(reply_rules_file),
        },
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stderr
    return recorded_argv.read_text().splitlines()


def carries_the_reply_rules(argv: list[str]) -> bool:
    return "--append-system-prompt" in argv


class TestSessionsAHumanDrives:
    def test_a_bare_invocation_carries_the_reply_rules(self, tmp_path):
        assert carries_the_reply_rules(run_launcher(tmp_path))

    def test_a_prompt_typed_at_the_keyboard_carries_the_reply_rules(self, tmp_path):
        assert carries_the_reply_rules(run_launcher(tmp_path, "fix the failing test"))

    def test_the_text_output_mode_carries_the_reply_rules(self, tmp_path):
        assert carries_the_reply_rules(run_launcher(tmp_path, "--mode", "text"))

    def test_the_rules_file_is_passed_as_a_path_ahead_of_the_user_arguments(
        self, tmp_path
    ):
        argv = run_launcher(tmp_path, "fix the failing test")
        assert argv[0] == "--append-system-prompt"
        assert argv[1].endswith("interactive-reply-rules.md")
        assert argv[2] == "fix the failing test"


class TestRunsNoHumanReads:
    def test_print_mode_is_left_alone(self, tmp_path):
        assert not carries_the_reply_rules(run_launcher(tmp_path, "-p", "summarize"))

    def test_the_long_print_flag_is_left_alone(self, tmp_path):
        assert not carries_the_reply_rules(
            run_launcher(tmp_path, "--print", "summarize")
        )

    def test_the_json_output_mode_is_left_alone(self, tmp_path):
        assert not carries_the_reply_rules(run_launcher(tmp_path, "--mode", "json"))

    def test_the_rpc_output_mode_is_left_alone(self, tmp_path):
        assert not carries_the_reply_rules(run_launcher(tmp_path, "--mode", "rpc"))

    def test_subcommands_are_left_alone(self, tmp_path):
        for subcommand in ("install", "remove", "uninstall", "update", "list", "auth"):
            assert not carries_the_reply_rules(run_launcher(tmp_path, subcommand))

    def test_version_and_help_are_left_alone(self, tmp_path):
        assert not carries_the_reply_rules(run_launcher(tmp_path, "--version"))
        assert not carries_the_reply_rules(run_launcher(tmp_path, "--help"))


class TestArgumentsReachPiUntouched:
    def test_every_user_argument_survives_in_order(self, tmp_path):
        argv = run_launcher(tmp_path, "-p", "--model", "anthropic/opus", "do the thing")
        assert argv == ["-p", "--model", "anthropic/opus", "do the thing"]
