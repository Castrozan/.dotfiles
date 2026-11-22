import argparse
import json
from pathlib import Path

TOPICS_DIRECTORY = Path(__file__).resolve().parent.parent / "topics"
AVATAR_ROOT_PLACEHOLDER = "{AVATAR_ROOT}"
STANDARDS_FILE_PLACEHOLDER = "{STANDARDS_FILE}"


def parse_command_line():
    parser = argparse.ArgumentParser(
        prog="avatar-rust-analysis-topics",
        description="Write analysis topic briefs with paths filled in.",
    )
    parser.add_argument("--avatar-root", required=True, help="avatar checkout")
    parser.add_argument("--standards-file", required=True, help="standards file")
    parser.add_argument("--output-directory", required=True, help="output root")
    return parser.parse_args()


def validation_error(arguments):
    if not Path(arguments.avatar_root).is_dir():
        return f"avatar root is not a directory: {arguments.avatar_root}"
    if not Path(arguments.standards_file).is_file():
        return f"standards file is missing: {arguments.standards_file}"
    return ""


def render_topic(template_text, arguments):
    return template_text.replace(
        AVATAR_ROOT_PLACEHOLDER, arguments.avatar_root
    ).replace(STANDARDS_FILE_PLACEHOLDER, arguments.standards_file)


def write_topic(template_path, arguments):
    topics_output_directory = Path(arguments.output_directory).resolve() / "topics"
    topics_output_directory.mkdir(parents=True, exist_ok=True)
    topic_path = topics_output_directory / template_path.name
    template_text = template_path.read_text(encoding="utf-8")
    topic_path.write_text(render_topic(template_text, arguments), encoding="utf-8")
    return str(topic_path)


def print_result(topics, error):
    print(json.dumps({"topics": topics, "error": error}))


def main():
    arguments = parse_command_line()
    error = validation_error(arguments)
    if error:
        print_result([], error)
        return
    template_paths = sorted(TOPICS_DIRECTORY.glob("*.md"))
    print_result([write_topic(path, arguments) for path in template_paths], "")


if __name__ == "__main__":
    main()
