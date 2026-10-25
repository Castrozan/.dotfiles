import subprocess
from dataclasses import dataclass
from pathlib import Path

TIMED_OUT_RETURN_CODE = 124
MISSING_COMMAND_RETURN_CODE = 127


@dataclass(frozen=True)
class CommandResult:
    return_code: int
    stdout: str
    diagnostics: str = ""

    @property
    def succeeded(self) -> bool:
        return self.return_code == 0

    @property
    def output(self) -> str:
        return self.stdout.strip()

    @property
    def explanation(self) -> str:
        return (self.diagnostics or self.stdout).strip()[-400:]


class CommandRunner:
    def run(
        self, arguments: list[str], directory: Path, timeout_seconds: int
    ) -> CommandResult:
        try:
            completed = subprocess.run(
                arguments,
                cwd=directory,
                stdin=subprocess.DEVNULL,
                capture_output=True,
                text=True,
                timeout=timeout_seconds,
                check=False,
            )
        except subprocess.TimeoutExpired:
            return CommandResult(
                TIMED_OUT_RETURN_CODE, "", f"timeout after {timeout_seconds}s"
            )
        except FileNotFoundError as error:
            return CommandResult(MISSING_COMMAND_RETURN_CODE, "", str(error))
        return CommandResult(completed.returncode, completed.stdout, completed.stderr)

    def run_capturing(
        self, arguments: list[str], directory: Path, timeout_seconds: int
    ) -> tuple[int, str]:
        result = self.run(arguments, directory, timeout_seconds)
        return result.return_code, result.output

    def launch_detached(
        self, arguments: list[str], directory: Path, log_path: Path
    ) -> None:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with log_path.open("w") as log:
            subprocess.Popen(
                arguments,
                cwd=directory,
                stdin=subprocess.DEVNULL,
                stdout=log,
                stderr=subprocess.STDOUT,
                start_new_session=True,
            )
