import os
import tomllib


def runtime_owned_ui_keys_preserved_across_rebuilds():
    keys = ["agent_panel_sort"]
    if os.environ.get("HERDR_RUNTIME_OWNS_ACCENT") == "1":
        keys.append("accent")
    return tuple(keys)


def read_preserved_ui_values(live_config_path):
    if not os.path.exists(live_config_path):
        return {}
    try:
        with open(live_config_path, "rb") as live_config_file:
            live_config = tomllib.load(live_config_file)
    except (tomllib.TOMLDecodeError, OSError):
        return {}
    live_ui_table = live_config.get("ui", {})
    return {
        key: live_ui_table[key]
        for key in runtime_owned_ui_keys_preserved_across_rebuilds()
        if key in live_ui_table
    }


def format_toml_scalar(value):
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, str):
        escaped = value.replace("\\", "\\\\").replace('"', '\\"')
        return f'"{escaped}"'
    return str(value)


def assignment_key_of_line(line):
    if "=" not in line:
        return None
    return line.split("=", 1)[0].strip()


def inject_preserved_ui_values_into_nix_source(nix_source_text, preserved_ui_values):
    if not preserved_ui_values:
        return nix_source_text
    lines = nix_source_text.splitlines()
    ui_header_index = next(
        (index for index, line in enumerate(lines) if line.strip() == "[ui]"),
        None,
    )
    if ui_header_index is None:
        raise SystemExit("herdr nix-source config has no [ui] section to seed into")
    ui_section_end_index = len(lines)
    for index in range(ui_header_index + 1, len(lines)):
        if lines[index].lstrip().startswith("["):
            ui_section_end_index = index
            break
    preserved_keys = set(preserved_ui_values)
    kept_ui_body_lines = [
        line
        for line in lines[ui_header_index + 1 : ui_section_end_index]
        if assignment_key_of_line(line) not in preserved_keys
    ]
    injected_ui_lines = [
        f"{key} = {format_toml_scalar(value)}"
        for key, value in preserved_ui_values.items()
    ]
    merged_lines = (
        lines[: ui_header_index + 1]
        + injected_ui_lines
        + kept_ui_body_lines
        + lines[ui_section_end_index:]
    )
    return "\n".join(merged_lines) + "\n"


def write_when_changed(target_path, desired_text):
    existing_text = None
    if os.path.exists(target_path):
        with open(target_path, encoding="utf-8") as target_file:
            existing_text = target_file.read()
    if existing_text != desired_text:
        temporary_path = f"{target_path}.tmp"
        with open(temporary_path, "w", encoding="utf-8") as temporary_file:
            temporary_file.write(desired_text)
        os.replace(temporary_path, target_path)
    os.chmod(target_path, 0o600)


def main():
    nix_source_path = os.environ["HERDR_NIX_SOURCE"]
    target_path = os.environ["HERDR_CONFIG"]
    if not os.path.exists(nix_source_path):
        return
    with open(nix_source_path, encoding="utf-8") as nix_source_file:
        nix_source_text = nix_source_file.read()
    preserved_ui_values = read_preserved_ui_values(target_path)
    merged_text = inject_preserved_ui_values_into_nix_source(
        nix_source_text, preserved_ui_values
    )
    write_when_changed(target_path, merged_text)


if __name__ == "__main__":
    main()
