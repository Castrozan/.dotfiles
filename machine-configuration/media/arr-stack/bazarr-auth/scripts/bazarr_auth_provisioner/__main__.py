import os
import subprocess
import tempfile

from bazarr_auth_config import (
    apply_forms_login,
    auth_already_matches,
    md5_hex,
    parse_auth_block,
)


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
    if auth_already_matches(parse_auth_block(config_lines), username, password_hash):
        print("bazarr-auth: already up to date")
        return
    was_running = container_is_running(container_name)
    if was_running:
        stop_container(container_name)
        config_lines = load_config_lines(config_file_path) or config_lines
    write_config_lines(
        config_file_path,
        apply_forms_login(config_lines, username, password_hash),
        owner_uid,
        owner_gid,
    )
    if was_running:
        start_container(container_name)
    print(f"bazarr-auth: forms login set for '{username}'")


if __name__ == "__main__":
    main()
