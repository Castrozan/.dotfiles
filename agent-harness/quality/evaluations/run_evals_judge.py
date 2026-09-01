import re


class JudgeInvocationError(RuntimeError):
    pass


def parse_judge_verdict(raw_verdict: str) -> tuple[bool, str]:
    stripped = raw_verdict.strip()
    if not stripped:
        return False, "no verdict"

    for line in reversed(stripped.splitlines()):
        verdict = re.search(r"\bVERDICT:\s*(PASS|FAIL)\b", line, re.IGNORECASE)
        if verdict:
            passed = verdict.group(1).upper() == "PASS"
            return passed, line.strip()

    first_line = stripped.splitlines()[0].strip()
    return bool(re.match(r"PASS\b", first_line, re.IGNORECASE)), first_line


def build_llm_judge(model: str | None, cli_invoker):
    def judge(rubric: str, output: str) -> tuple[bool, str]:
        judge_prompt = (
            "You grade an AI assistant response against ONE rubric. "
            "Reason in one or two sentences about whether the response satisfies "
            "the rubric, then on the final line write exactly 'VERDICT: PASS' or "
            "'VERDICT: FAIL'. Grade only against the rubric, not style or length.\n\n"
            f"Rubric: {rubric}\n\n"
            f"Response under evaluation:\n{output}"
        )
        raw_verdict, invoked = cli_invoker(judge_prompt, model=model, no_tools=True)
        if not invoked:
            raise JudgeInvocationError(f"judge invocation failed: {raw_verdict[:120]}")
        return parse_judge_verdict(raw_verdict)

    return judge
