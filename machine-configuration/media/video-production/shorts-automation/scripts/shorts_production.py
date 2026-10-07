import argparse
import json
import os
from pathlib import Path

import shorts_runner
from shorts_quality import digest, inside_run, verify_episode, verify_publication
from shorts_store import (
    PUBLICATION_FILENAME,
    RUN_STATUS_FILENAME,
    TopicStore,
    read_document,
    timestamp,
    write_document,
)


def state_directory():
    return Path(os.environ.get("SHORTS_STATE_DIRECTORY", Path.home() / "clawde/shorts"))


def run_directory(root):
    directory = Path.cwd().resolve()
    if directory.parent != (root / "runs").resolve():
        raise ValueError("Run this command inside a scheduled episode directory")
    return directory


def verified_video(directory, episode):
    proof = read_document(directory / "verification.json")
    video = inside_run(directory, episode["video"])
    if proof["sha256"] != digest(video):
        raise ValueError("Video changed after verification")
    return proof


def record_dispatch(directory, proof):
    journal = directory / PUBLICATION_FILENAME
    if journal.exists():
        raise ValueError("Publication was already dispatched; inspect before retrying")
    write_document(journal, {"status": "dispatch_recorded", "sha256": proof["sha256"]})
    return {"status": "dispatch_recorded"}


def complete_episode(directory, store, episode):
    publication = read_document(directory / PUBLICATION_FILENAME)
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
    write_document(directory / PUBLICATION_FILENAME, publication)
    write_document(directory / RUN_STATUS_FILENAME, publication)
    return publication


def episode_command(action, root, path):
    directory = run_directory(root)
    episode = read_document(inside_run(directory, path))
    store = TopicStore(root)
    if action == "reserve":
        return {
            "topic_key": store.reserve(episode, directory.name),
            "status": "reserved",
        }
    store.reservation(directory.name, episode["topic_key"])
    if action == "verify":
        proof = verify_episode(directory, episode)
        write_document(directory / "verification.json", proof)
        return proof
    proof = verified_video(directory, episode)
    if action == "dispatch":
        return record_dispatch(directory, proof)
    return complete_episode(directory, store, episode)


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
        result = shorts_runner.start_run(
            root, arguments.slot, read_document(os.environ["SHORTS_CONFIGURATION"])
        )
    elif arguments.action == "history":
        result = TopicStore(root).history()
    else:
        result = episode_command(arguments.action, root, arguments.episode_file)
    print(json.dumps(result))


if __name__ == "__main__":
    main()
