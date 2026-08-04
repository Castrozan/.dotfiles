import os
import sys
from pathlib import Path

API_KEY_PLACEHOLDER = "@OPENCODE_GO_API_KEY@"
RENDERED_CONFIGURATION_MODE = 0o600
MISSING_ARGUMENTS_EXIT_CODE = 2
UNUSABLE_API_KEY_EXIT_CODE = 1


def render_proxy_configuration(template_text: str, api_key: str) -> str:
    if API_KEY_PLACEHOLDER not in template_text:
        raise ValueError(
            f"the configuration template must carry {API_KEY_PLACEHOLDER} so the key can be injected at runtime"
        )
    return template_text.replace(API_KEY_PLACEHOLDER, api_key)


def read_api_key(api_key_path: Path) -> str:
    api_key = api_key_path.read_text().strip()
    if not api_key:
        raise ValueError(f"the API key at {api_key_path} is empty")
    return api_key


def write_owner_readable_file(destination_path: Path, contents: str) -> None:
    destination_path.parent.mkdir(parents=True, exist_ok=True)
    file_descriptor = os.open(
        destination_path,
        os.O_WRONLY | os.O_CREAT | os.O_TRUNC,
        RENDERED_CONFIGURATION_MODE,
    )
    with os.fdopen(file_descriptor, "w") as destination_file:
        destination_file.write(contents)


def render_configuration_then_exec_proxy(
    template_path: Path,
    api_key_path: Path,
    rendered_configuration_path: Path,
    proxy_arguments: list[str],
    exec_program=os.execv,
) -> int:
    try:
        api_key = read_api_key(api_key_path)
    except (OSError, ValueError) as unusable_api_key:
        print(
            f"claude-go proxy: {unusable_api_key}; deploy the opencode-api-key agenix secret",
            file=sys.stderr,
        )
        return UNUSABLE_API_KEY_EXIT_CODE

    write_owner_readable_file(
        rendered_configuration_path,
        render_proxy_configuration(template_path.read_text(), api_key),
    )
    exec_program(proxy_arguments[0], proxy_arguments)
    return 0


def main() -> int:
    if len(sys.argv) < 5:
        return MISSING_ARGUMENTS_EXIT_CODE

    return render_configuration_then_exec_proxy(
        Path(sys.argv[1]),
        Path(sys.argv[2]),
        Path(sys.argv[3]),
        sys.argv[4:],
    )


if __name__ == "__main__":
    sys.exit(main())
