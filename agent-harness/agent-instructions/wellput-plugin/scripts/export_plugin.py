import ast
import importlib.metadata
import importlib.util
import json
import re
import shutil
import stat
import sys
from pathlib import Path


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


def portable_references(text, core_path, docs_path):
    text = re.sub(r"(?:\.\./)+core-rules/core\.md", core_path, text)
    return text.replace("Use the `docs` skill", f"Read [artifact writing]({docs_path})")


def export_instructions(sources, output):
    skill = Path(sources["skill"])
    destination = output / "skills/wellput"
    copy_directory(skill, destination)
    for relative, core_path, docs_path in (
        ("SKILL.md", "references/core.md", "references/artifact-writing.md"),
        ("references/interactive-communication.md", "core.md", "artifact-writing.md"),
    ):
        path = destination / relative
        text = portable_references(path.read_text(), core_path, docs_path)
        text = text.replace(
            "so WezTerm can detect them", "so terminals can detect them"
        )
        text = text.replace(
            "Use\n`url-shortener` for long public references; keep artifact URLs direct.",
            "Keep artifact URLs direct.",
        )
        path.write_text(
            text.replace("Humanize", "Wellput").replace("humanize", "wellput")
        )
    core = Path(sources["core"]).read_text()
    sections = re.split(r"(?=^### )", core, flags=re.MULTILINE)
    selected = [
        section
        for section in sections
        if section.startswith(("### Evidence\n", "### Autonomy\n", "### Completion\n"))
    ]
    write_file(destination, "references/core.md", "".join(selected).rstrip() + "\n")
    docs = Path(sources["docs"]).read_text()
    docs = docs[docs.index("### Never write") :]
    write_file(
        destination,
        "references/artifact-writing.md",
        docs.replace("humanize", "wellput"),
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


def export_tests(sources, output):
    shutil.copyfile(
        Path(sources["portableTests"]) / "test_hooks.py", output / "tests/test_hooks.py"
    )
    shutil.copyfile(sources["verifier"], output / "tests/verify_plugin.py")
    tests = Path(sources["tests"])
    for name in (
        "test_human_facing_reply_rules.py",
        "test_reply_format_configuration.py",
        "test_reply_markdown_structure.py",
        "test_reply_quotation_performance.py",
    ):
        text = (
            (tests / name)
            .read_text()
            .replace(
                'REPLY_RULE_MODULE_DIRECTORY / "reply-formats.json"',
                'REPLY_RULE_MODULE_DIRECTORY.parents[1] / "wellput.json"',
            )
        )
        write_file(output, f"tests/{name}", text)
    support = Path(sources["support"]).read_text()
    start = support.index("HOOKS_ROOT =")
    end = support.index("LABELED_REPLY =")
    support = (
        support[:start]
        + 'REPLY_RULE_MODULE_DIRECTORY = Path(__file__).resolve().parents[1] / "hooks/rules"\nsys.path.insert(0, str(REPLY_RULE_MODULE_DIRECTORY))\nsys.path.insert(0, str(REPLY_RULE_MODULE_DIRECTORY.parent / "vendor"))\n\nfrom reply_rule_catalog import template_violations_in_reply\nfrom reply_rule_feedback import bounce_guidance\n\n'
        + support[end:]
    )
    write_file(output, "tests/human_facing_reply_test_support.py", support)


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
