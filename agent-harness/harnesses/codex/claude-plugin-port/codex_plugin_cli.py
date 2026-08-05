import subprocess
import tomllib

from configuration import (
    CODEX_COMMAND_TIMEOUT_SECONDS,
    PORTED_MARKETPLACE_NAME,
    codex_config_path,
    resolve_codex_binary,
)

codex_binary = resolve_codex_binary()


def run_codex_plugin_command(arguments):
    if codex_binary is None:
        return 1, "", "codex binary not found"
    try:
        completed_process = subprocess.run(
            [str(codex_binary), "plugin", *arguments],
            capture_output=True,
            text=True,
            timeout=CODEX_COMMAND_TIMEOUT_SECONDS,
        )
        return (
            completed_process.returncode,
            completed_process.stdout.strip(),
            completed_process.stderr.strip(),
        )
    except (subprocess.TimeoutExpired, OSError) as command_error:
        return 1, "", str(command_error)


def read_codex_config():
    if not codex_config_path.exists():
        return {}
    try:
        return tomllib.loads(codex_config_path.read_text())
    except (tomllib.TOMLDecodeError, OSError):
        return {}


def previously_ported_plugin_names():
    ported_suffix = f"@{PORTED_MARKETPLACE_NAME}"
    return {
        plugin_key.split("@", 1)[0]
        for plugin_key in read_codex_config().get("plugins", {})
        if plugin_key.endswith(ported_suffix)
    }


def ported_marketplace_is_registered():
    return PORTED_MARKETPLACE_NAME in read_codex_config().get("marketplaces", {})
