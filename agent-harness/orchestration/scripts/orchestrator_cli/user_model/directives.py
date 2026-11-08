from __future__ import annotations

import re
from dataclasses import dataclass, replace
from datetime import date
from pathlib import Path

from ..document_fields import InvalidPeerDocument

DIRECTIVE_KINDS = ("Always", "Never", "Prefer")
FIELD_SEPARATOR = " · "
DIRECTIVE_LINE_PATTERN = re.compile(
    r"^- (?P<identifier>U-\d{3,}) · (?P<status>active|superseded by U-\d{3,}) · "
    r"(?P<recorded>\d{4}-\d{2}-\d{2}) · scope: (?P<scope>[^·]+?) · "
    r"(?P<kind>Always|Never|Prefer) (?P<rule>[^·]+?) · source: (?P<source>.+)$"
)


@dataclass(frozen=True)
class Directive:
    identifier: str
    status: str
    recorded: str
    scope: str
    kind: str
    rule: str
    source: str

    @property
    def active(self) -> bool:
        return self.status == "active"

    def line(self) -> str:
        return FIELD_SEPARATOR.join(
            [
                f"- {self.identifier}",
                self.status,
                self.recorded,
                f"scope: {self.scope}",
                f"{self.kind} {self.rule}",
                f"source: {self.source}",
            ]
        )


def default_user_model_path() -> Path:
    return Path(
        "~/.dotfiles/private-configuration/agent-harness/user-model/USER.md"
    ).expanduser()


def parsed_directives(text: str) -> list[Directive]:
    return [
        Directive(**match.groupdict())
        for match in map(DIRECTIVE_LINE_PATTERN.match, text.splitlines())
        if match
    ]


def read_directives(path: Path) -> list[Directive]:
    if not path.is_file():
        raise InvalidPeerDocument(f"no user model at {path}")
    return parsed_directives(path.read_text(encoding="utf-8"))


def active_identifiers(path: Path) -> set[str]:
    return {
        directive.identifier for directive in read_directives(path) if directive.active
    }


def clean_field(value: str, description: str) -> str:
    cleaned = " ".join(value.split())
    if not cleaned or "·" in cleaned:
        raise InvalidPeerDocument(f"{description} must be nonempty and free of '·'")
    return cleaned


def next_identifier(directives: list[Directive]) -> str:
    numbers = [int(directive.identifier[2:]) for directive in directives]
    return f"U-{max(numbers, default=0) + 1:03d}"


def new_directive(
    directives: list[Directive], kind: str, scope: str, rule: str, source: str
) -> Directive:
    if kind not in DIRECTIVE_KINDS:
        raise InvalidPeerDocument(f"kind must be one of {', '.join(DIRECTIVE_KINDS)}")
    return Directive(
        identifier=next_identifier(directives),
        status="active",
        recorded=date.today().isoformat(),
        scope=clean_field(scope, "scope"),
        kind=kind,
        rule=clean_field(rule, "rule").rstrip("."),
        source=clean_field(source, "source"),
    )


def rewritten_text(text: str, changed: dict[str, Directive], added: Directive) -> str:
    lines = []
    for line in text.rstrip("\n").splitlines():
        match = DIRECTIVE_LINE_PATTERN.match(line)
        identifier = match["identifier"] if match else None
        lines.append(changed[identifier].line() if identifier in changed else line)
    return "\n".join([*lines, added.line()]) + "\n"


def append_directive(path: Path, directive_fields: dict) -> Directive:
    text = path.read_text(encoding="utf-8")
    added = new_directive(parsed_directives(text), **directive_fields)
    path.write_text(rewritten_text(text, {}, added), encoding="utf-8")
    return added


def supersede_directive(
    path: Path, identifier: str, directive_fields: dict
) -> Directive:
    text = path.read_text(encoding="utf-8")
    directives = parsed_directives(text)
    current = {directive.identifier: directive for directive in directives}.get(
        identifier
    )
    if current is None or not current.active:
        raise InvalidPeerDocument(f"{identifier} is not an active directive")
    added = new_directive(directives, **directive_fields)
    retired = replace(current, status=f"superseded by {added.identifier}")
    path.write_text(
        rewritten_text(text, {identifier: retired}, added), encoding="utf-8"
    )
    return added
