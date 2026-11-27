import subprocess
import sys
import tomllib
from pathlib import Path


def test_generates_the_default_profile_with_exact_instruction_contents(tmp_path):
    instructions_path = tmp_path / "instructions.md"
    profile_path = tmp_path / "dotfiles-interactive.config.toml"
    instructions = 'First line with "quotes", \\ and café\r\n\r\nSecond line\n'
    instructions_path.write_bytes(instructions.encode())
    generator = (
        Path(__file__).parents[2] / "scripts" / "generate_interactive_profile.py"
    )

    subprocess.run(
        [sys.executable, generator, instructions_path, profile_path],
        check=True,
        timeout=10,
    )

    with profile_path.open("rb") as profile:
        assert tomllib.load(profile) == {"developer_instructions": instructions}
