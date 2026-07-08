import subprocess

from runtime_environment import log


def compose_base_command(
    docker_compose_binary, compose_file, env_file, project_directory, project_name
):
    return [
        docker_compose_binary,
        "--file",
        compose_file,
        "--env-file",
        env_file,
        "--project-directory",
        project_directory,
        "--project-name",
        project_name,
    ]


def running_on_demand_services(base_command, on_demand_services):
    completed = subprocess.run(
        base_command + ["ps", "--services", "--filter", "status=running"],
        capture_output=True,
        text=True,
        check=False,
    )
    return set(completed.stdout.split()) & set(on_demand_services)


def start_on_demand_services(base_command, on_demand_services, dry_run):
    if dry_run:
        log(f"[dry-run] would start chain: {' '.join(on_demand_services)}")
        return
    subprocess.run(base_command + ["up", "--detach"] + on_demand_services, check=True)


def stop_on_demand_services(base_command, on_demand_services, dry_run):
    if dry_run:
        log(f"[dry-run] would stop chain: {' '.join(on_demand_services)}")
        return
    subprocess.run(base_command + ["stop"] + on_demand_services, check=True)


def read_last_active_epoch(state_file_path):
    try:
        with open(state_file_path, encoding="utf-8") as handle:
            return float(handle.read().strip())
    except (FileNotFoundError, ValueError):
        return None


def write_last_active_epoch(state_file_path, now_epoch):
    with open(state_file_path, "w", encoding="utf-8") as handle:
        handle.write(str(now_epoch))
