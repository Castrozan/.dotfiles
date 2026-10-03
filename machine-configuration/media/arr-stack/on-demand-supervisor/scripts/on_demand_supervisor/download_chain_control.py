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


def services_not_held(services, held_services):
    return [service for service in services if service not in held_services]


def keep_always_on_services_running(
    base_command,
    on_demand_services,
    effective_services,
    dry_run,
    running_services,
    start_services,
    log_message,
):
    running = running_services(base_command, on_demand_services)
    missing_services = [
        service for service in effective_services if service not in running
    ]
    if missing_services:
        log_message(
            f"keep-chain-always-on: starting missing services {missing_services}"
        )
        start_services(base_command, effective_services, dry_run)
    else:
        log_message("keep-chain-always-on: full chain up, holding")


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
