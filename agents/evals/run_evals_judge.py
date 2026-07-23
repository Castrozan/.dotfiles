def parse_judge_verdict(raw_verdict: str) -> tuple[bool, str]:
    stripped = raw_verdict.strip()
    if not stripped:
        return False, "no verdict"

    for line in reversed(stripped.splitlines()):
        if "VERDICT:" in line.upper():
            after_marker = line.upper().split("VERDICT:", 1)[1]
            passed = "PASS" in after_marker and "FAIL" not in after_marker
            return passed, line.strip()

    first_line = stripped.splitlines()[0].strip()
    return first_line.upper().startswith("PASS"), first_line


def build_llm_judge(model: str, cli_invoker):
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
            return False, f"judge invocation failed: {raw_verdict[:120]}"
        return parse_judge_verdict(raw_verdict)

    return judge
