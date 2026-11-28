import tarfile
from pathlib import PurePosixPath

from agent_api_job.errors import JobError
from agent_api_job.model import validate_tree_key
from agent_api_job.storage import private_directory, read_json, write_json

DEFAULT_MAXIMUM_BYTES = 512 * 1024 * 1024


def safe_member_name(member):
    path = PurePosixPath(member.name)
    if path.is_absolute() or ".." in path.parts:
        raise JobError("unsafe_member")
    return str(path)


def extract_members(archive, tree, maximum_bytes):
    delivered = []
    total_bytes = 0
    for member in archive:
        name = safe_member_name(member)
        total_bytes += member.size
        if total_bytes > maximum_bytes:
            raise JobError("tree_too_large")
        archive.extract(member, path=tree, filter="data")
        if not member.isdir():
            delivered.append(name)
    return delivered


def removable(path, resolved_tree):
    inside = path.parent.resolve().is_relative_to(resolved_tree)
    return inside and (path.is_symlink() or path.is_file())


def remove_stale(tree, previous, delivered):
    resolved_tree = tree.resolve()
    for name in set(previous) - set(delivered):
        path = tree / name
        if removable(path, resolved_tree):
            path.unlink()


def receive_tree(root, key, stream, maximum_bytes):
    validate_tree_key(key)
    trees = private_directory(private_directory(root) / "trees")
    tree = trees / key
    tree.mkdir(mode=0o700, exist_ok=True)
    manifest = trees / f"{key}.manifest"
    previous = read_json(manifest) or []
    try:
        with tarfile.open(fileobj=stream, mode="r|") as archive:
            delivered = extract_members(archive, tree, maximum_bytes)
    except tarfile.TarError:
        raise JobError("unsafe_member") from None
    remove_stale(tree, previous, delivered)
    write_json(manifest, delivered)
    return {"tree": key, "files": len(delivered)}
