from benchmark_baseline import BaselineValidation

REPORT_SEPARATOR_WIDTH = 60


def baseline_report_lines(title: str, validation: BaselineValidation) -> list[str]:
    document = validation.document
    separator = "=" * REPORT_SEPARATOR_WIDTH
    age = "unknown" if validation.age_days is None else f"{validation.age_days} days"
    host = document.get("host", "unknown")
    configuration = document.get("config", "unknown")
    lines = [
        separator,
        title,
        separator,
        f"  Generated: {document.get('generated_at', 'unknown')}",
        f"  Age: {age}",
        f"  Commit: {document.get('git_commit', 'unknown')}",
        f"  Host: {host}/{configuration}",
        f"  Threshold: {document.get('threshold_percent', '?')}%",
    ]
    if validation.failures:
        lines.append("")
        lines.append(f"FAILED ({len(validation.failures)} issues):")
        lines.extend(f"  - {failure}" for failure in validation.failures)
    return lines
