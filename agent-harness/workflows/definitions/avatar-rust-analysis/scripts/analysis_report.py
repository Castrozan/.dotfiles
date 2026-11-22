import argparse
import json
import sys
from pathlib import Path

NO_REPORTS = {"reports": 0, "research_json": "", "research_markdown": ""}


def parse_command_line():
    parser = argparse.ArgumentParser(
        prog="avatar-rust-analysis-report",
        description="Assemble topic research results read from stdin into one report.",
    )
    parser.add_argument(
        "--output-directory", required=True, help="directory that receives the reports"
    )
    return parser.parse_args()


def research_results_of(document):
    if isinstance(document, list):
        return document
    if isinstance(document, dict):
        return next(
            (value for value in document.values() if isinstance(value, list)), []
        )
    return []


def read_research_results():
    try:
        document = json.load(sys.stdin)
    except ValueError:
        return None
    return research_results_of(document)


def decision_text(entry):
    return f"{entry['decision']} ({entry['reason']}) [{' '.join(entry['sources'])}]"


def render_section(result):
    lines = [f"## {result['topic']}", ""]
    lines.extend(f"- {decision_text(entry)}" for entry in result["decisions"])
    lines.extend(["", "Rejected:"])
    lines.extend(f"- {item}" for item in result["rejected"])
    lines.extend(["", "Unknown:"])
    lines.extend(f"- {item}" for item in result["unknowns"])
    return "\n".join(lines) + "\n"


def succeeded(results):
    return [result for result in results if "topic" in result]


def render_markdown(results):
    return "\n".join(render_section(result) for result in succeeded(results))


def write_reports(results, output_directory):
    output_directory.mkdir(parents=True, exist_ok=True)
    research_json = output_directory / "research.json"
    research_markdown = output_directory / "research.md"
    research_json.write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")
    research_markdown.write_text(render_markdown(results), encoding="utf-8")
    return research_json, research_markdown


def print_result(results, research_json, research_markdown):
    print(
        json.dumps(
            {
                "reports": len(succeeded(results)),
                "failed": len(results) - len(succeeded(results)),
                "research_json": str(research_json),
                "research_markdown": str(research_markdown),
            }
        )
    )


def main():
    arguments = parse_command_line()
    results = read_research_results()
    if results is None:
        print(json.dumps(NO_REPORTS))
        return
    paths = write_reports(results, Path(arguments.output_directory).resolve())
    print_result(results, *paths)


if __name__ == "__main__":
    main()
