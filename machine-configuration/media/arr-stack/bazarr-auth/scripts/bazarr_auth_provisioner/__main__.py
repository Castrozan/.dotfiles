import os
import subprocess
import tempfile
from dataclasses import dataclass

from bazarr_auth_config import (
    apply_forms_login,
    auth_already_matches,
    md5_hex,
    parse_auth_block,
)


@dataclass
class AuthConfigUpdateRequest:
    config_file_path: str
    config_lines: list
    container_name: str
    username: str
    password_hash: str
    owner_uid: int
    owner_gid: int


def read_secret_value(secret_file_path):
    if not secret_file_path:
        return ""
    try:
        with open(secret_file_path, encoding="utf-8") as handle:
            return handle.read().strip()
    except FileNotFoundError:
        return ""


def load_config_lines(config_file_path):
    try:
        with open(config_file_path, encoding="utf-8") as handle:
            return handle.read().splitlines()
    except FileNotFoundError:
        return None


def write_config_lines(config_file_path, config_lines, owner_uid, owner_gid):
    directory = os.path.dirname(config_file_path)
    descriptor, temporary_path = tempfile.mkstemp(dir=directory)
    with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
        handle.write("\n".join(config_lines) + "\n")
    os.chown(temporary_path, owner_uid, owner_gid)
    os.chmod(temporary_path, 0o644)
    os.replace(temporary_path, config_file_path)


def container_is_running(container_name):
    result = subprocess.run(
        ["docker", "inspect", "-f", "{{.State.Running}}", container_name],
        capture_output=True,
        text=True,
    )
    return result.returncode == 0 and result.stdout.strip() == "true"


def stop_container(container_name):
    subprocess.run(["docker", "stop", container_name], check=True)


def start_container(container_name):
    subprocess.run(["docker", "start", container_name], check=True)


def parse_owner(owner_value):
    owner_uid, owner_gid = (int(part) for part in owner_value.split(":"))
    return owner_uid, owner_gid


def _authentication_matches_config(config_lines, username, password_hash):
    return auth_already_matches(parse_auth_block(config_lines), username, password_hash)


def _update_config_while_container_is_running(request):
    was_running = container_is_running(request.container_name)
    if was_running:
        stop_container(request.container_name)
        request.config_lines = (
            load_config_lines(request.config_file_path) or request.config_lines
        )
    write_config_lines(
        request.config_file_path,
        apply_forms_login(
            request.config_lines, request.username, request.password_hash
        ),
        request.owner_uid,
        request.owner_gid,
    )
    if was_running:
        start_container(request.container_name)


def main():
    config_file_path = os.environ["BAZARR_AUTH_CONFIG_FILE"]
    container_name = os.environ["BAZARR_AUTH_CONTAINER_NAME"]
    username = os.environ.get("BAZARR_AUTH_LOGIN_USERNAME", "")
    password = read_secret_value(os.environ.get("BAZARR_AUTH_PASSWORD_FILE", ""))
    owner_uid, owner_gid = parse_owner(
        os.environ.get("BAZARR_AUTH_FILE_OWNER", "1000:100")
    )
    if not username or not password:
        print("bazarr-auth: skipped, username or password not provided")
        return
    password_hash = md5_hex(password)
    config_lines = load_config_lines(config_file_path)
    if config_lines is None:
        print("bazarr-auth: skipped, config file not present yet")
        return
    if _authentication_matches_config(config_lines, username, password_hash):
        print("bazarr-auth: already up to date")
        return
    _update_config_while_container_is_running(
        AuthConfigUpdateRequest(
            config_file_path,
            config_lines,
            container_name,
            username,
            password_hash,
            owner_uid,
            owner_gid,
        )
    )
    print(f"bazarr-auth: forms login set for '{username}'")


if __name__ == "__main__":
    main()
