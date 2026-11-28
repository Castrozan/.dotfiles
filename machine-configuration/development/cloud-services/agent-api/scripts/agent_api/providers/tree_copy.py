import hashlib
import os
import subprocess
import tempfile

from agent_api.contract import CapabilityError
from agent_api.inventory import self_name
from agent_api.providers.host_transport import HOST_TIMEOUT_SECONDS, run_job


def tree_key(directory):
    return hashlib.sha256(f"{self_name()}:{directory}".encode()).hexdigest()[:32]


def is_file_entry(directory, relative_path):
    path = os.path.join(directory, relative_path)
    return os.path.lexists(path) and (os.path.islink(path) or not os.path.isdir(path))


def listed_files(directory):
    try:
        completed = subprocess.run(
            ["git", "-C", directory, "ls-files", "-co", "--exclude-standard", "-z"],
            stdin=subprocess.DEVNULL,
            capture_output=True,
            check=False,
            timeout=HOST_TIMEOUT_SECONDS,
        )
    except (OSError, subprocess.TimeoutExpired):
        raise CapabilityError("directory_not_a_repository") from None
    if completed.returncode != 0:
        raise CapabilityError("directory_not_a_repository")
    names = completed.stdout.decode(errors="surrogateescape").split("\0")
    return [name for name in names if name and is_file_entry(directory, name)]


def write_listing(listing, names):
    for name in names:
        listing.write(name.encode(errors="surrogateescape") + b"\0")
    listing.seek(0)


def copy_tree(entry, directory):
    key = tree_key(directory)
    with tempfile.TemporaryFile() as listing:
        write_listing(listing, listed_files(directory))
        archive = subprocess.Popen(
            ["tar", "-C", directory, "--null", "-T", "-", "-cf", "-"],
            stdin=listing,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
        )
        try:
            run_job(entry, ["receive", key], stdin=archive.stdout)
        finally:
            archive.stdout.close()
            try:
                archive.wait(timeout=HOST_TIMEOUT_SECONDS)
            except subprocess.TimeoutExpired:
                archive.kill()
                archive.wait()
    if archive.returncode != 0:
        raise CapabilityError("tree_copy_failed")
    return key
