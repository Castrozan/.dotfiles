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
        try:
            destination = urlsplit(urljoin(source.absolute().as_uri(), link.target))
            path = Path(unquote(destination.path, errors="strict"))
            anchor = unquote(destination.fragment, errors="strict")
            if destination.scheme in {"http", "https"} and not destination.hostname:
                raise ValueError("expected a URL hostname")
        except ValueError:
            violations.append(
                InstructionFormatViolation(
                    "instruction_link_destination",
                    link.line_number,
                    f"expected a valid link destination: {link.target}",
                )
            )
            continue
        if destination.scheme != "file":
            continue
        physical_path = filesystem_root / path.relative_to(path.anchor)
        if destination.netloc or not physical_path.is_file():
            violations.append(
                InstructionFormatViolation(
                    "instruction_link_file",
                    link.line_number,
                    f"expected an existing local file: {link.target}",
                )
            )
            continue
        if not anchor:
            continue
        try:
            if path not in inspections:
                inspections[path] = inspect_markdown_instruction(
                    physical_path.read_text(encoding="utf-8")
                )
            if anchor in inspections[path].anchors:
                continue
        except (OSError, UnicodeError):
            pass
        violations.append(
            InstructionFormatViolation(
                "instruction_link_anchor",
                link.line_number,
                f"expected an existing heading anchor: {link.target}",
            )
        )
    return violations
