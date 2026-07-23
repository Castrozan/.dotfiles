def build_llm_judge(model: str, cli_invoker):
    def judge(rubric: str, output: str) -> tuple[bool, str]:
        judge_prompt = (
            "You are grading an AI assistant response against a single rubric. "
            "Reply with PASS or FAIL as the first word, then a one-sentence reason.\n\n"
            f"Rubric: {rubric}\n\n"
            f"Response under evaluation:\n{output}"
        )
        verdict, invoked = cli_invoker(judge_prompt, model=model, no_tools=True)
        if not invoked:
            return False, f"judge invocation failed: {verdict[:120]}"
        stripped_verdict = verdict.strip()
        passed = stripped_verdict.upper().startswith("PASS")
        reason = stripped_verdict.splitlines()[0] if stripped_verdict else "no verdict"
        return passed, reason

    return judge
