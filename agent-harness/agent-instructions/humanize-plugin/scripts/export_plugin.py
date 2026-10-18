import ast
import importlib.metadata
import importlib.util
import json
import re
import shutil
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


def portable_references(text, core_path, docs_path):
    text = re.sub(r"(?:\.\./)+core-rules/core\.md", core_path, text)
    return text.replace("Use the `docs` skill", f"Read [artifact writing]({docs_path})")


def export_instructions(sources, output):
    skill = Path(sources["skill"])
    destination = output / "skills/humanize"
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
        path.write_text(text)
    core = Path(sources["core"]).read_text()
    sections = re.split(r"(?=^### )", core, flags=re.MULTILINE)
    selected = [
        section
        for section in sections
        if section.startswith(("### Evidence\n", "### Autonomy\n", "### Completion\n"))
    ]
    write_file(destination, "references/core.md", "".join(selected))
    docs = Path(sources["docs"]).read_text()
    docs = docs[docs.index("### Never write") :]
    write_file(destination, "references/artifact-writing.md", docs)
    evaluation = (skill / "__tests__/evals/reader_recovery.yaml").read_text()
    evaluation = evaluation.replace(
        "agent-harness/agent-instructions/skills/writing/humanize/", "skills/humanize/"
    )
    write_file(output, "evals/reader_recovery.yaml", evaluation)


def export_runtime(sources, output):
    copy_directory(Path(sources["rules"]), output / "hooks/rules")
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
    renderer = Path(sources["renderer"]).read_text()
    renderer = renderer.replace(
        "from instructions.instruction_surface_scanner import REPO_ROOT",
        "REPO_ROOT = Path(__file__).resolve().parent",
    )
    renderer = renderer.replace(
        "agent-harness/hooks/runtime/common/human_facing_reply/reply-formats.json",
        "rules/reply-formats.json",
    )
    write_file(output, "hooks/reply_format_instructions.py", renderer)
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
    tests = Path(sources["tests"])
    for name in (
        "test_human_facing_reply_rules.py",
        "test_reply_format_configuration.py",
        "test_reply_markdown_structure.py",
        "test_reply_quotation_performance.py",
    ):
        shutil.copyfile(tests / name, output / "tests" / name)
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
