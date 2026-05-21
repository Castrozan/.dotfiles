"""Run the haiku review subprocess with multi-round liveness polling."""

import subprocess

from end_of_work_compliance_review_logging import log_status

SECONDS_PER_MINUTE = 60

REVIEW_WAIT_INTERVAL_MINUTES_PER_ROUND = [2, 2, 4]

KILL_GRACE_PERIOD_SECONDS = 5


def run_review_subprocess_with_liveness_polling(
    review_command: list[str], subprocess_environment: dict
) -> str | None:
    review_subprocess = subprocess.Popen(
        review_command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=subprocess_environment,
    )

    total_rounds = len(REVIEW_WAIT_INTERVAL_MINUTES_PER_ROUND)
    cumulative_wait_minutes = 0

    for round_index, wait_minutes_for_round in enumerate(
        REVIEW_WAIT_INTERVAL_MINUTES_PER_ROUND
    ):
        cumulative_wait_minutes += wait_minutes_for_round
        round_number = round_index + 1
        wait_seconds_for_round = wait_minutes_for_round * SECONDS_PER_MINUTE

        try:
            stdout_from_review, _ = review_subprocess.communicate(
                timeout=wait_seconds_for_round
            )
            return stdout_from_review
        except subprocess.TimeoutExpired:
            is_final_round = round_number == total_rounds
            if is_final_round:
                review_subprocess.kill()
                try:
                    review_subprocess.communicate(timeout=KILL_GRACE_PERIOD_SECONDS)
                except subprocess.TimeoutExpired:
                    pass
                log_status(
                    f"killed haiku subprocess after {cumulative_wait_minutes}min "
                    f"total wait ({total_rounds} rounds)"
                )
                return None
            log_status(
                f"haiku still alive after round {round_number}/{total_rounds} "
                f"({wait_minutes_for_round}min, {cumulative_wait_minutes}min total), "
                f"continuing"
            )

    return None
