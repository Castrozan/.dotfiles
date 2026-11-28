import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from reports import report_replay, report_summary, report_tools  # noqa: E402
from session_parsing import load_sessions  # noqa: E402


def main():
    parser = argparse.ArgumentParser(
        description="Measure where Claude Code tokens go from session transcripts."
    )
    parser.add_argument("report", choices=("summary", "tools", "replay"))
    parser.add_argument("--days", type=int, default=14)
    parser.add_argument("--current-threshold", type=int, default=400_000)
    arguments = parser.parse_args()
    sessions = load_sessions(arguments.days)
    if arguments.report == "summary":
        report_summary(sessions)
    elif arguments.report == "tools":
        report_tools(sessions)
    else:
        report_replay(sessions, arguments.current_threshold)


if __name__ == "__main__":
    main()
