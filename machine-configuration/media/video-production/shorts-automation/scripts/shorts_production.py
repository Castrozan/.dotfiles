import argparse
import fcntl
import json
import os
import signal
import subprocess
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from shorts_quality import digest, inside_run, verify_episode, verify_publication
from shorts_store import TopicStore, read_document, timestamp, write_document


def state_directory():
    return Path(os.environ.get("SHORTS_STATE_DIRECTORY", Path.home() / "clawde/shorts"))


def run_directory(root):
    directory = Path.cwd().resolve()
    if directory.parent != (root / "runs").resolve():
        raise ValueError("Run this command inside a scheduled episode directory")
    return directory


def start_run(root, slot, configuration):
    root.mkdir(parents=True, exist_ok=True, mode=0o700)
    with (root / "production.lock").open("w") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return {"status": "skipped", "reason": "Another production run is active"}
        now = datetime.now(ZoneInfo(configuration["timezone"]))
        selected = slot or now.hour
        if selected not in configuration["hours"]:
            return {"status": "skipped", "reason": "Outside scheduled production slots"}
        identifier = f"{now.date()}-{selected:02d}00"
        directory = root / "runs" / identifier
        if directory.exists():
            return {
                "status": "skipped",
                "reason": "Slot already claimed",
                "run_id": identifier,
            }
        directory.mkdir(parents=True, mode=0o700)
        store = TopicStore(root)
        write_document(directory / "history.json", store.history())
        write_document(directory / "config.json", configuration)
        write_document(
            directory / "status.json", {"status": "started", "started_at": timestamp()}
        )
        arguments = [
            os.environ["SHORTS_CODEX"],
            "exec",
            "--skip-git-repo-check",
            "-C",
            str(directory),
            "--model",
            configuration["model"],
            "-c",
            'model_reasoning_effort="high"',
            "-c",
            'web_search="live"',
            "-c",
            "mcp_servers.chrome-devtools.enabled=false",
            "-c",
            'plugins."betha-chrome-devtools@betha-agent-marketplace".mcp_servers.chrome-devtools.enabled=false',
            "-c",
            'plugins."betha-desenvolvimento@betha-agent-marketplace".mcp_servers.chrome-devtools.enabled=false',
            "-c",
            'approval_policy="never"',
            "--sandbox",
            "danger-full-access",
            "--json",
            "--output-last-message",
            str(directory / "agent-result.txt"),
            Path(os.environ["SHORTS_GOAL_PROMPT"]).read_text().strip(),
        ]
        with (directory / "agent-events.jsonl").open("w") as output:
            process = subprocess.Popen(
                arguments,
                stdout=output,
                stderr=subprocess.STDOUT,
                start_new_session=True,
            )
            try:
                returncode = process.wait(timeout=7200)
                status = "agent_finished" if returncode == 0 else "needs_inspection"
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGTERM)
                try:
                    process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    os.killpg(process.pid, signal.SIGKILL)
                    process.wait()
                status = "needs_inspection"
        previous = read_document(directory / "status.json")
        if previous["status"] == "published":
            return previous
        if (directory / "hold.json").is_file():
            status = "held"
        previous.update(status=status, finished_at=timestamp())
        write_document(directory / "status.json", previous)
        return previous


def episode_command(action, root, path):
    directory = run_directory(root)
    store = TopicStore(root)
    episode = read_document(path)
    if action == "reserve":
        key = store.reserve(episode, directory.name)
        return {"topic_key": key, "status": "reserved"}
    store.reservation(directory.name, episode["topic_key"])
    if action == "verify":
        proof = verify_episode(directory, episode)
        write_document(directory / "verification.json", proof)
        return proof
    proof = read_document(directory / "verification.json")
    video = inside_run(directory, episode["video"])
    if proof["sha256"] != digest(video):
        raise ValueError("Video changed after verification")
    if action == "dispatch":
        journal = directory / "publication.json"
        if journal.exists():
            raise ValueError(
                "Publication was already dispatched; inspect before retrying"
            )
        write_document(
            journal, {"status": "dispatch_recorded", "sha256": proof["sha256"]}
        )
        return {"status": "dispatch_recorded"}
    publication = read_document(directory / "publication.json")
    if publication["status"] != "dispatch_recorded":
        raise ValueError("Expected a single recorded publication dispatch")
    configuration = read_document(directory / "config.json")
    video_id = verify_publication(episode["url"], configuration["channel_id"])
    store.publish(directory.name, video_id)
    publication.update(
        status="published",
        url=episode["url"],
        video_id=video_id,
        published_at=timestamp(),
    )
    write_document(directory / "publication.json", publication)
    write_document(directory / "status.json", publication)
    return publication


def main():
    os.umask(0o077)
    parser = argparse.ArgumentParser()
    commands = parser.add_subparsers(dest="action", required=True)
    run = commands.add_parser("run")
    run.add_argument("--slot", type=int, choices=[9, 15, 21])
    commands.add_parser("history")
    for action in ("reserve", "verify", "dispatch", "complete"):
        commands.add_parser(action).add_argument(
            "--episode-file", type=Path, required=True
        )
    arguments = parser.parse_args()
    root = state_directory()
    if arguments.action == "run":
        result = start_run(
            root, arguments.slot, read_document(os.environ["SHORTS_CONFIGURATION"])
        )
    elif arguments.action == "history":
        result = TopicStore(root).history()
    else:
        result = episode_command(arguments.action, root, arguments.episode_file)
    print(json.dumps(result))


if __name__ == "__main__":
    main()
