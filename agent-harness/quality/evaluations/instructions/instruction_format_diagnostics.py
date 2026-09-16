from dataclasses import dataclass


@dataclass(frozen=True)
class InstructionFormatViolation:
    rule: str
    line_number: int | None
    detail: str

    def render(self) -> str:
        location = f"line {self.line_number}: " if self.line_number else ""
        return f"{self.rule}: {location}{self.detail}"
