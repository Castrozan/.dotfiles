from pathlib import Path
from urllib.parse import unquote, urljoin, urlsplit

from instructions.instruction_format_diagnostics import InstructionFormatViolation
from instructions.ai_instruction_format import (
    InstructionInspection,
    inspect_markdown_instruction,
)


def instruction_link_violations(
    source: Path,
    inspection: InstructionInspection,
    inspections: dict[Path, InstructionInspection],
    filesystem_root: Path = Path("/"),
) -> list[InstructionFormatViolation]:
    violations = []
    for link in inspection.links:
        violations.extend(_link_violations(source, link, inspections, filesystem_root))
    return violations


def _link_violations(source, link, inspections, filesystem_root):
    parsed_link = _parse_link_destination(source, link)
    if parsed_link is None:
        return [_link_destination_violation(link)]
    destination, path, anchor = parsed_link
    if destination.scheme != "file":
        return []
    physical_path = filesystem_root / path.relative_to(path.anchor)
    file_violation = _local_link_file_violation(destination, link, physical_path)
    if file_violation:
        return [file_violation]
    return _anchor_violation(path, anchor, physical_path, inspections, link)


def _anchor_violation(path, anchor, physical_path, inspections, link):
    if not anchor or _link_anchor_exists(path, anchor, physical_path, inspections):
        return []
    return [_missing_link_anchor_violation(link)]


def _parse_link_destination(source, link):
    try:
        destination = urlsplit(urljoin(source.absolute().as_uri(), link.target))
        path = Path(unquote(destination.path, errors="strict"))
        anchor = unquote(destination.fragment, errors="strict")
        if destination.scheme in {"http", "https"} and not destination.hostname:
            raise ValueError("expected a URL hostname")
    except ValueError:
        return None
    return destination, path, anchor


def _link_destination_violation(link):
    return InstructionFormatViolation(
        "instruction_link_destination",
        link.line_number,
        f"expected a valid link destination: {link.target}",
    )


def _local_link_file_violation(destination, link, physical_path):
    if not destination.netloc and physical_path.is_file():
        return None
    return InstructionFormatViolation(
        "instruction_link_file",
        link.line_number,
        f"expected an existing local file: {link.target}",
    )


def _link_anchor_exists(path, anchor, physical_path, inspections):
    try:
        if path not in inspections:
            inspections[path] = inspect_markdown_instruction(
                physical_path.read_text(encoding="utf-8")
            )
        return anchor in inspections[path].anchors
    except (OSError, UnicodeError):
        return False


def _missing_link_anchor_violation(link):
    return InstructionFormatViolation(
        "instruction_link_anchor",
        link.line_number,
        f"expected an existing heading anchor: {link.target}",
    )
