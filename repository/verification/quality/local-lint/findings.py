from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from hashlib import sha256
import json


@dataclass(frozen=True)
class Finding:
    tool: str
    rule: str
    path: str
    line: int
    message: str
    identity: str
    score: int


def issue_finding(issue):
    location = issue["location"]
    source = issue.get("snippet", "").strip()
    score = int(issue.get("properties", {}).get("actual", 1))
    if issue.get("driver") == "structure":
        source = source.splitlines()[0] if source else issue["message"]
    related_paths = sorted(entry["path"] for entry in issue.get("otherLocations", []))
    identity = json.dumps(
        [issue["tool"], issue["ruleKey"], location["path"], source, related_paths],
        sort_keys=True,
    )
    return Finding(
        issue["tool"],
        issue["ruleKey"],
        location["path"],
        location.get("range", {}).get("startLine", 1),
        issue["message"],
        sha256(identity.encode()).hexdigest(),
        score,
    )


def complexity_finding(statistics):
    identity = json.dumps(
        ["cyclomatic", statistics["path"], statistics["fullyQualifiedName"]]
    )
    score = statistics["cyclomatic"]
    return Finding(
        "qlty",
        "cyclomatic-complexity",
        statistics["path"],
        1,
        f"{statistics['fullyQualifiedName']} has cyclomatic complexity {score} (maximum 5)",
        sha256(identity.encode()).hexdigest(),
        score,
    )


def collect_findings(reports):
    findings = [
        issue_finding(issue)
        for name in ("lint", "smells")
        for issue in reports.get(name, [])
    ]
    findings.extend(
        complexity_finding(statistics)
        for statistics in reports.get("complexity", {"stats": []})["stats"]
        if statistics.get("kind") == "COMPONENT_TYPE_FUNCTION"
        and statistics.get("cyclomatic", 0) > 5
    )
    return sorted(findings, key=lambda entry: (entry.path, entry.line, entry.rule))


def baseline_entries(findings):
    counts = Counter((finding.identity, finding.score) for finding in findings)
    return [
        {"identity": identity, "score": score, "count": count}
        for (identity, score), count in sorted(counts.items())
    ]


def consume_recorded_ceiling(ceilings, score):
    for ceiling in sorted(ceilings):
        if ceiling < score:
            continue
        if ceilings[ceiling] == 0:
            continue
        ceilings[ceiling] -= 1
        return True
    return False


def baseline_allowance(entry):
    identity, score, count = entry["identity"], entry["score"], entry["count"]
    if not isinstance(identity, str):
        raise ValueError("Baseline identity must be a string")
    for value, minimum in ((score, 0), (count, 1)):
        if type(value) is not int:
            raise ValueError("Baseline scores and counts must be integers")
        if value < minimum:
            raise ValueError("Baseline score or count is below its minimum")
    return identity, score, count


def new_findings(findings, baseline):
    available = defaultdict(Counter)
    for entry in baseline:
        identity, score, count = baseline_allowance(entry)
        available[identity][score] += count
    violations = []
    for finding in sorted(findings, key=lambda entry: entry.score, reverse=True):
        if not consume_recorded_ceiling(available[finding.identity], finding.score):
            violations.append(finding)
    return violations


def report_data(findings, violations, failures):
    return {
        "findings": [asdict(finding) for finding in findings],
        "newFindings": [asdict(finding) for finding in violations],
        "errors": failures,
        "passed": not violations and not failures,
    }
