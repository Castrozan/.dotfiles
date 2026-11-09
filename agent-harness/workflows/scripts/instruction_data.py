import argparse
import json
import os
import sys


def instruction_data(value) -> str:
    serialized = json.dumps(value, ensure_ascii=False, separators=(",", ":"))
    return "`" + serialized.replace("`", "\\u0060") + "`"


def parse_command_line(command_line_arguments: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="instruction-data",
        description=(
            "Print the named environment variables as one inline-code JSON span "
            "each, so a value can never change the prompt around it."
        ),
    )
    parser.add_argument("--text", nargs="*", default=[], metavar="VARIABLE")
    parser.add_argument("--json", nargs="*", default=[], metavar="VARIABLE")
    return parser.parse_args(command_line_arguments)


def field_name(variable_name: str) -> str:
    return variable_name.lower().removeprefix("inputs_")


def serialized_values(
    text_variables: list[str], json_variables: list[str], environment: dict[str, str]
) -> dict[str, str]:
    values = {name: environment.get(name, "") for name in text_variables} | {
        name: json.loads(environment.get(name) or "null") for name in json_variables
    }
    return {field_name(name): instruction_data(value) for name, value in values.items()}


def main() -> int:
    arguments = parse_command_line(sys.argv[1:])
    print(json.dumps(serialized_values(arguments.text, arguments.json, os.environ)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
