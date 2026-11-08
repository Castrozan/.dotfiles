from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from second_brain.index import (
    ATLAS_DIRECTORY_NAME,
    ENTRY_DIRECTORY_NAME,
    second_brain_directory,
)

CONTRIBUTING_FILE_NAME = "CONTRIBUTING.md"
TAG_LEGEND_FILE_NAME = "Tag Legend.md"
TEMPLATE_REFERENCE = re.compile(r"`(templates/[^`]+\.md)`")
TAG_VALUE = re.compile(r"`#([a-z0-9-]+/[a-z0-9-]+)`")
TOPIC_PREFIX = "topic/"


class ContractUnreadable(RuntimeError):
    pass


@dataclass(frozen=True)
class SecondBrainContract:
    entry_directory: Path
    atlas_directory: Path
    template_text: str
    tag_values: frozenset[str]


def required_text(path: Path) -> str:
    if not path.is_file():
        raise ContractUnreadable(f"the Second Brain contract needs {path}")
    return path.read_text(encoding="utf-8")


def read_contract(vault_directory: Path) -> SecondBrainContract:
    second_brain = second_brain_directory(vault_directory)
    contributing = required_text(second_brain / CONTRIBUTING_FILE_NAME)
    template_reference = TEMPLATE_REFERENCE.search(contributing)
    if template_reference is None:
        raise ContractUnreadable("CONTRIBUTING.md names no entry template")
    atlas_directory = second_brain / ATLAS_DIRECTORY_NAME
    tag_legend = required_text(atlas_directory / TAG_LEGEND_FILE_NAME)
    return SecondBrainContract(
        entry_directory=second_brain / ENTRY_DIRECTORY_NAME,
        atlas_directory=atlas_directory,
        template_text=required_text(second_brain / template_reference.group(1)),
        tag_values=frozenset(TAG_VALUE.findall(tag_legend)),
    )


def entry_tag_problems(tags: list[str], contract: SecondBrainContract) -> list[str]:
    unknown_tags = [tag for tag in tags if tag not in contract.tag_values]
    topic_count = sum(tag.startswith(TOPIC_PREFIX) for tag in tags)
    problems = [f"tag {tag} is not in the Tag Legend" for tag in unknown_tags]
    if topic_count != 1:
        problems.append(f"an entry carries exactly one topic tag, found {topic_count}")
    return problems
