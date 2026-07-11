from disk_space_guard import enforce_disk_space_guard
from download_activity import arr_download_queue_active, arr_service_reachable
from download_chain_control import (
    read_last_active_epoch,
    running_on_demand_services,
    start_on_demand_services,
    stop_on_demand_services,
    write_last_active_epoch,
)
from jellyseerr_client import actionable_requests, retry_request
from mount_health_guard import enforce_data_mount_guard
from runtime_environment import log, read_arr_api_key_from_config_xml


def held_down_services_from_disk_guard(configuration, base_command, now_epoch, dry_run):
    disk_guard = configuration.get("disk_guard")
    if not disk_guard:
        return []
    return enforce_disk_space_guard(disk_guard, base_command, now_epoch, dry_run)


def keep_chain_up_for_actionable_requests(
    jellyseerr_url,
    jellyseerr_api_key,
    base_command,
    on_demand_services,
    state_file_path,
    now_epoch,
    radarr_url,
    recent_pending_request_ids,
    failed_request_ids,
    radarr_running,
    dry_run,
):
    if not radarr_running:
        log(
            f"actionable requests (pending={len(recent_pending_request_ids)} "
            f"failed={len(failed_request_ids)}); starting chain"
        )
        start_on_demand_services(base_command, on_demand_services, dry_run)
    write_last_active_epoch(state_file_path, now_epoch)
    if failed_request_ids and arr_service_reachable(radarr_url):
        for request_id in failed_request_ids:
            if dry_run:
                log(f"[dry-run] would retry failed request {request_id}")
                continue
            retry_status = retry_request(jellyseerr_url, jellyseerr_api_key, request_id)
            log(f"retried failed request {request_id} -> {retry_status}")
    elif failed_request_ids:
        log("chain starting; deferring retry of failed requests until radarr is ready")


def stop_chain_when_idle_past_grace(
    base_command,
    on_demand_services,
    state_file_path,
    now_epoch,
    idle_grace_seconds,
    arr_endpoints,
    dry_run,
):
    if arr_download_queue_active(arr_endpoints):
        write_last_active_epoch(state_file_path, now_epoch)
        log("download queue active; keeping chain up")
        return
    last_active_epoch = read_last_active_epoch(state_file_path)
    if last_active_epoch is None:
        write_last_active_epoch(state_file_path, now_epoch)
        log(
            "no idle baseline recorded yet; recording now and keeping chain up this tick"
        )
        return
    idle_seconds = now_epoch - last_active_epoch
    if idle_seconds >= idle_grace_seconds:
        log(f"idle {int(idle_seconds)}s >= grace {idle_grace_seconds}s; stopping chain")
        stop_on_demand_services(base_command, on_demand_services, dry_run)
    else:
        log(
            f"idle {int(idle_seconds)}s < grace {idle_grace_seconds}s; keeping chain up"
        )


def run_supervisor_tick(configuration, now_epoch, dry_run):
    base_command = configuration["base_command"]
    if enforce_data_mount_guard(configuration, base_command, now_epoch, dry_run):
        return
    on_demand_services = configuration["on_demand_services"]
    state_file_path = configuration["state_file_path"]
    jellyseerr_url = configuration["jellyseerr_url"]
    jellyseerr_api_key = configuration["jellyseerr_api_key"]
    radarr_url = configuration["radarr_url"]
    sonarr_url = configuration["sonarr_url"]

    held_down_services = held_down_services_from_disk_guard(
        configuration, base_command, now_epoch, dry_run
    )
    effective_services = [
        service for service in on_demand_services if service not in held_down_services
    ]

    if configuration["keep_chain_always_on"]:
        running = running_on_demand_services(base_command, on_demand_services)
        missing_services = [
            service for service in effective_services if service not in running
        ]
        if missing_services:
            log(f"keep-chain-always-on: starting missing services {missing_services}")
            start_on_demand_services(base_command, effective_services, dry_run)
        else:
            log("keep-chain-always-on: full chain up, holding")
        write_last_active_epoch(state_file_path, now_epoch)
        return

    recent_pending_request_ids, failed_request_ids = actionable_requests(
        jellyseerr_url,
        jellyseerr_api_key,
        now_epoch,
        configuration["recent_pending_window_seconds"],
    )
    chain_should_be_up = bool(recent_pending_request_ids) or bool(failed_request_ids)
    running = running_on_demand_services(base_command, on_demand_services)
    radarr_running = "radarr" in running

    if chain_should_be_up:
        keep_chain_up_for_actionable_requests(
            jellyseerr_url,
            jellyseerr_api_key,
            base_command,
            effective_services,
            state_file_path,
            now_epoch,
            radarr_url,
            recent_pending_request_ids,
            failed_request_ids,
            radarr_running,
            dry_run,
        )
        return

    if not radarr_running:
        log("no actionable requests and chain is down; nothing to do")
        return

    arr_endpoints = [
        (
            radarr_url,
            read_arr_api_key_from_config_xml(configuration["radarr_config_file"]),
        ),
        (
            sonarr_url,
            read_arr_api_key_from_config_xml(configuration["sonarr_config_file"]),
        ),
    ]
    stop_chain_when_idle_past_grace(
        base_command,
        on_demand_services,
        state_file_path,
        now_epoch,
        configuration["idle_grace_seconds"],
        arr_endpoints,
        dry_run,
    )
