import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

from agent_commit_provenance.commit_trailers import (
    AGENT_HARNESS_TRAILER_KEY,
    AGENT_MACHINE_TRAILER_KEY,
    AGENT_NAME_TRAILER_KEY,
    AGENT_RESUME_TRAILER_KEY,
    AGENT_SESSION_TRAILER_KEY,
    parse_agent_provenance_trailers,
)
from agent_commit_provenance.session_identity import machine_name_from_environment
from agent_commit_provenance.transcript_locations import (
    transcript_path_for_session,
    user_prompts_in_transcript,
)

PROMPT_PREVIEW_CHARACTER_LIMIT = 400


def commit_subject_and_message(commit_reference: str) -> tuple[str, str]:
    commit_read = subprocess.run(
        ["git", "log", "-1", "--format=%h %s%n%n%B", commit_reference],
        capture_output=True,
        text=True,
        check=False,
    )
    if commit_read.returncode != 0:
        raise SystemExit(
            commit_read.stderr.strip() or f"unknown commit: {commit_reference}"
        )
    header, _separator, message = commit_read.stdout.partition("\n\n")
    return header.strip(), message


def provenance_report(commit_reference: str) -> dict[str, object]:
    header, message = commit_subject_and_message(commit_reference)
    recorded_trailers = parse_agent_provenance_trailers(message)
    harness_name = recorded_trailers.get(AGENT_HARNESS_TRAILER_KEY)
    session_identifier = recorded_trailers.get(AGENT_SESSION_TRAILER_KEY)
    transcript_path = (
        transcript_path_for_session(harness_name, session_identifier)
        if harness_name and session_identifier
        else None
    )
    return {
        "commit": header,
        "harness": harness_name,
        "machine": recorded_trailers.get(AGENT_MACHINE_TRAILER_KEY),
        "agent": recorded_trailers.get(AGENT_NAME_TRAILER_KEY),
        "session": session_identifier,
        "resume": recorded_trailers.get(AGENT_RESUME_TRAILER_KEY),
        "transcript": str(transcript_path) if transcript_path else None,
    }


def print_human_report(report: dict[str, object]) -> None:
    current_machine_name = machine_name_from_environment(os.environ)
    recorded_machine_name = report["machine"]
    machine_description = str(recorded_machine_name)
    if recorded_machine_name != current_machine_name:
        machine_description = f"{recorded_machine_name} (run the resume command there)"
    print(f"commit      {report['commit']}")
    print(f"harness     {report['harness']}")
    print(f"machine     {machine_description}")
    if report["agent"]:
        print(f"agent       {report['agent']}")
    print(f"session     {report['session']}")
    print(f"resume      {report['resume']}")
    transcript = report["transcript"]
    if transcript:
        transcript_size_megabytes = Path(str(transcript)).stat().st_size / 1_000_000
        print(f"transcript  {transcript} ({transcript_size_megabytes:.1f} MB)")
    elif recorded_machine_name == current_machine_name:
        print("transcript  not on disk, the harness pruned it")
    else:
        print(f"transcript  on {recorded_machine_name}")


def print_user_prompts(report: dict[str, object]) -> None:
    transcript = report["transcript"]
    if not transcript:
        return
    prompts = user_prompts_in_transcript(str(report["harness"]), Path(str(transcript)))
    for prompt_number, prompt in enumerate(prompts, start=1):
        preview = prompt.strip()
        if len(preview) > PROMPT_PREVIEW_CHARACTER_LIMIT:
            preview = f"{preview[:PROMPT_PREVIEW_CHARACTER_LIMIT]}..."
        print()
        print(f"prompt {prompt_number}")
        print(preview)


def parse_arguments(command_line_arguments: list[str]) -> argparse.Namespace:
    argument_parser = argparse.ArgumentParser(
        prog="git agent-session",
        description="show which agent session produced a commit and how to resume it",
    )
    argument_parser.add_argument("commit", nargs="?", default="HEAD")
    argument_parser.add_argument("--json", action="store_true", dest="emit_json")
    argument_parser.add_argument("--prompts", action="store_true", dest="show_prompts")
    return argument_parser.parse_args(command_line_arguments)


def main(command_line_arguments: list[str]) -> int:
    arguments = parse_arguments(command_line_arguments)
    report = provenance_report(arguments.commit)
    if arguments.emit_json:
        print(json.dumps(report, indent=2))
        return 0 if report["session"] else 1
    if not report["session"]:
        print(f"{report['commit']}")
        print(
            "no agent session recorded, this commit was made by hand or before tracking"
        )
        return 1
    print_human_report(report)
    if arguments.show_prompts:
        print_user_prompts(report)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
