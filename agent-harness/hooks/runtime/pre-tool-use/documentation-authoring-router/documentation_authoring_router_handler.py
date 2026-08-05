from __future__ import annotations

import os
import sys

_MODULE_DIRECTORY = os.path.dirname(os.path.realpath(__file__))
_ANCESTOR_DIRECTORY = _MODULE_DIRECTORY
_SHARED_MODULE_CANDIDATE_DIRECTORIES = [_MODULE_DIRECTORY]
while _ANCESTOR_DIRECTORY != os.path.dirname(_ANCESTOR_DIRECTORY):
    _ANCESTOR_DIRECTORY = os.path.dirname(_ANCESTOR_DIRECTORY)
    _SHARED_MODULE_CANDIDATE_DIRECTORIES.append(
        os.path.join(_ANCESTOR_DIRECTORY, "common")
    )
for _shared_module_candidate_directory in _SHARED_MODULE_CANDIDATE_DIRECTORIES:
    if (
        os.path.isdir(_shared_module_candidate_directory)
        and _shared_module_candidate_directory not in sys.path
    ):
        sys.path.insert(0, _shared_module_candidate_directory)

import skill_loaded_marker  # noqa: E402
from changed_file_paths import collect_changed_file_paths  # noqa: E402
from file_path_components import path_components  # noqa: E402
from hook_dispatch import HandlerResult  # noqa: E402

DOCUMENTATION_FILENAME_ALWAYS_A_DOCUMENT = "readme.md"

DOCUMENTATION_DIRECTORY_PARTS = {"docs", "documentation"}

VENDORED_TREE_DIRECTORY_PARTS = {
    "node_modules",
    ".terraform",
    ".direnv",
    ".venv",
    "vendor",
}

DOCUMENTATION_AUTHORING_DIRECTIVE = (
    "BLOCKED: this file is user-facing documentation, so it must be authored against the "
    "documentation standards. This guard blocks every edit to a README or a file under a "
    "docs/ directory until you have loaded those standards into context this session by "
    "invoking Skill(skill='docs') for when a doc earns its place, what never to write, "
    "evergreen phrasing, and policy shape. Once you have invoked Skill(skill='docs') this "
    "session, re-attempt this edit applying those standards and it will proceed."
)


def has_loaded_docs_skill_this_session(session_id):
    return skill_loaded_marker.has_skill_loaded("docs", session_id)


def is_vendored_tree_path(path_parts):
    return any(part.lower() in VENDORED_TREE_DIRECTORY_PARTS for part in path_parts)


def is_documentation_file(file_path):
    if not file_path:
        return False
    path_parts = path_components(file_path)
    if is_vendored_tree_path(path_parts):
        return False
    if os.path.splitext(file_path)[1].lower() != ".md":
        return False
    if os.path.basename(file_path).lower() == DOCUMENTATION_FILENAME_ALWAYS_A_DOCUMENT:
        return True
    return any(part.lower() in DOCUMENTATION_DIRECTORY_PARTS for part in path_parts)


def handle(hook_input):
    edited_paths = collect_changed_file_paths(hook_input)
    if not any(is_documentation_file(path) for path in edited_paths):
        return None

    if has_loaded_docs_skill_this_session(hook_input.get("session_id", "")):
        return None

    return HandlerResult(decision="deny", reason=DOCUMENTATION_AUTHORING_DIRECTIVE)
