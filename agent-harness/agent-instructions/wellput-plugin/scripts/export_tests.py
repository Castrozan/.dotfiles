import shutil
from pathlib import Path


def export_tests(sources, output):
    for name in ("test_hooks.py", "test_exported_instructions.py"):
        shutil.copyfile(Path(sources["portableTests"]) / name, output / "tests" / name)
    shutil.copyfile(sources["verifier"], output / "tests/verify_plugin.py")
    tests_destination = output / "tests"
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
        (tests_destination / name).write_text(text, encoding="utf-8")
    support = Path(sources["support"]).read_text()
    start = support.index("HOOKS_ROOT =")
    end = support.index("LABELED_REPLY =")
    support = (
        support[:start]
        + 'REPLY_RULE_MODULE_DIRECTORY = Path(__file__).resolve().parents[1] / "hooks/rules"\nsys.path.insert(0, str(REPLY_RULE_MODULE_DIRECTORY))\nsys.path.insert(0, str(REPLY_RULE_MODULE_DIRECTORY.parent / "vendor"))\n\nfrom reply_rule_catalog import template_violations_in_reply\nfrom reply_rule_feedback import bounce_guidance\n\n'
        + support[end:]
    )
    (tests_destination / "human_facing_reply_test_support.py").write_text(
        support, encoding="utf-8"
    )
