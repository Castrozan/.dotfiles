def build_execution_profile(settings, subject_harness, judge_harness):
    return {
        "subject": {
            "harness": subject_harness,
            "model": settings["subject_models"][subject_harness],
            "reasoning_effort": settings.get("subject_reasoning_efforts", {}).get(
                subject_harness
            ),
        },
        "judge": {
            "harness": judge_harness,
            "model": settings["judge_models"][judge_harness],
            "reasoning_effort": settings.get("judge_reasoning_efforts", {}).get(
                judge_harness
            ),
        },
    }
