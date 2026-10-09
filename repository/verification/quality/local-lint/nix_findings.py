import json
import subprocess
import sys


def json_documents(output):
    decoder = json.JSONDecoder()
    remaining = output.strip()
    while remaining:
        document, end = decoder.raw_decode(remaining)
        yield document
        remaining = remaining[end:].strip()


def diagnostic(path, line, column, message, rule):
    return {
        "message": message,
        "severity": "WARNING",
        "code": {"value": rule},
        "location": {
            "path": path,
            "range": {"start": {"line": line, "column": column}},
        },
    }


def statix_report_diagnostics(path, report):
    for entry in report["diagnostics"]:
        position = entry["at"]["from"]
        yield diagnostic(
            path,
            position["line"],
            position["column"],
            entry["message"],
            f"statix-{report['code']}",
        )


def statix_diagnostics(documents):
    for document in documents:
        for report in document["report"]:
            yield from statix_report_diagnostics(document["file"], report)


def deadnix_diagnostics(documents):
    for document in documents:
        for entry in document["results"]:
            yield diagnostic(
                document["file"],
                entry["line"],
                entry["column"],
                entry["message"],
                "unused-binding",
            )


def main():
    tool, *paths = sys.argv[1:]
    commands = {
        "statix": ["statix", "check", "--format", "json", "--", *paths],
        "deadnix": ["deadnix", "--output-format", "json", "--", *paths],
    }
    parsers = {"statix": statix_diagnostics, "deadnix": deadnix_diagnostics}
    result = subprocess.run(commands[tool], capture_output=True, text=True, timeout=120)
    diagnostics = list(parsers[tool](json_documents(result.stdout)))
    if result.returncode not in (0, 1) or (result.returncode and not diagnostics):
        raise RuntimeError(result.stderr or f"{tool} failed without diagnostics")
    print(json.dumps({"diagnostics": diagnostics}))


if __name__ == "__main__":
    main()
