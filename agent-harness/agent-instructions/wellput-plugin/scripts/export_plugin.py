import ast
import importlib.metadata
import importlib.util
import json
import shutil
import stat
import sys
from pathlib import Path

from export_tests import export_tests
from portable_instructions import portable_session_policy, portable_skill


def write_file(root, relative, content):
    destination = root / relative
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(content, encoding="utf-8")


def copy_directory(source, destination):
    shutil.copytree(
        source,
        destination,
        dirs_exist_ok=True,
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "__tests__"),
    )
    for path in (destination, *destination.rglob("*")):
        path.chmod(path.stat().st_mode | stat.S_IWUSR)


def export_instructions(sources, output):
    sys.path.insert(0, str(sources["instructionFormatter"]))
    from instructions.instruction_prose_wrapping import wrap_instruction_prose

    skill = Path(sources["skill"])
    destination = output / "skills/wellput"
    copy_directory(skill, destination)
    for relative, project_policy in (
        ("SKILL.md", portable_skill),
        ("references/interactive-communication.md", portable_session_policy),
    ):
        path = destination / relative
        text = project_policy(path.read_text())
        text = text.replace(
            "so WezTerm can detect them", "so terminals can detect them"
        )
        text = text.replace(
            "Use\n`url-shortener` for long public references; keep artifact URLs direct.",
            "Keep artifact URLs direct.",
        )
        path.write_text(
            wrap_instruction_prose(
                text.replace("Humanize", "Wellput").replace("humanize", "wellput")
            )
        )
    evaluation = (skill / "__tests__/evals/reader_recovery.yaml").read_text()
    evaluation = evaluation.replace(
        "agent-harness/agent-instructions/skills/writing/humanize/", "skills/wellput/"
    )
    write_file(
        output, "evals/reader_recovery.yaml", evaluation.replace("Humanize", "Wellput")
    )


def export_transcript_reader(sources, output):
    guard = Path(sources["guard"]).read_text()
    reader_functions = []
    for node in ast.parse(guard).body:
        if not isinstance(node, ast.FunctionDef):
            continue
        if node.name == "_reply_format_validation_result":
            break
        reader_functions.append(ast.get_source_segment(guard, node))
    write_file(
        output,
        "hooks/transcript.py",
        "import json\nimport os\n\n\n" + "\n\n\n".join(reader_functions) + "\n",
    )


def export_runtime(sources, output):
    copy_directory(Path(sources["rules"]), output / "hooks/rules")
    configuration = output / "hooks/rules/reply-formats.json"
    write_file(
        output, "wellput.json", configuration.read_text().replace("Humanize", "Wellput")
    )
    configuration.unlink()
    configuration_module = output / "hooks/rules/reply_format_configuration.py"
    configuration_source = configuration_module.read_text().replace(
        "import json\nimport os\n",
        "from wellput_configuration import load_configuration_document\n",
    )
    configuration_source = configuration_source[
        : configuration_source.index("\nwith open(")
    ]
    configuration_module.write_text(
        configuration_source
        + "\nREPLY_FORMAT_DOCUMENT = load_configuration_document()\n"
        + "REPLY_FORMAT_CONFIGURATION = ReplyFormatConfiguration(REPLY_FORMAT_DOCUMENT)\n"
    )
    export_transcript_reader(sources, output)
    renderer = Path(sources["renderer"]).read_text()
    renderer = renderer[renderer.index("def expand_reply_format_instructions(") :]
    renderer = renderer.replace(
        "configuration = json.loads(\n            (REPO_ROOT / REPLY_FORMAT_CONFIGURATION_PATH).read_text()\n        )",
        "from reply_format_configuration import REPLY_FORMAT_DOCUMENT\n\n        configuration = REPLY_FORMAT_DOCUMENT",
    )
    write_file(
        output,
        "hooks/reply_format_instructions.py",
        'REPLY_FORMAT_PLACEHOLDER = "{{reply_format}}"\n\n\n' + renderer,
    )
    for module, distribution_name in (
        ("markdown_it", "markdown-it-py"),
        ("mdurl", "mdurl"),
    ):
        specification = importlib.util.find_spec(module)
        copy_directory(
            Path(specification.origin).parent, output / "hooks/vendor" / module
        )
        distribution = importlib.metadata.distribution(distribution_name)
        for path in distribution.files:
            if "LICENSE" in path.name:
                write_file(
                    output,
                    f"hooks/vendor/licenses/{distribution_name}/{path.name}",
                    distribution.locate_file(path).read_text(),
                )


def main():
    sources = json.loads(Path(sys.argv[1]).read_text())
    output = Path(sys.argv[2])
    if output.exists():
        raise ValueError(f"Refusing to replace an existing export: {output}")
    copy_directory(Path(sources["assets"]), output)
    export_instructions(sources, output)
    export_runtime(sources, output)
    export_tests(sources, output)


if __name__ == "__main__":
    main()
