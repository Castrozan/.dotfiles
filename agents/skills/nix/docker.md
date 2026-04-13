<invocation>
The docker-manager script lives at `agents/skills/nix/docker-scripts/docker-manager`. Run it with `--help` for the authoritative command reference. It is the curated interface — do not shell out to raw `docker` or `podman` commands even if they seem faster. The script enforces ordering (stop before remove), prevents data loss (volume backup before delete), and surfaces errors the daemon hides.
</invocation>

<safety_boundaries>
Common cascade trap: `docker rm` succeeds on stopped containers; `docker rmi` fails if a container still references the image. The script handles this cascade. A running or stopped container holds a reference to its image — removing the image fails until the container is removed. Image removal is idempotent only if the tag is unused; rebuilding with the same tag orphans the old image. Dangling images accumulate — the script's image-cleanup handles this, verify current prune policy before using it.
</safety_boundaries>

<container_state>
Containers have multiple states (created, running, paused, stopped, exiting, dead). Status checks are point-in-time snapshots — a container running at inspection time may crash milliseconds later. When scripting multi-step workflows (start, wait for healthcheck, then exec), insert actual waits, not just state queries. "Container is running" does not mean "ready to accept traffic."
</container_state>

<execution_in_containers>
`docker exec` works only on running containers. If exec must happen regardless of state, use the script's container-ensure-running helper or wrap the exec with explicit start logic. Exit codes from exec are reliable; container logs are not (buffering, log driver limits). When debugging failed execs, check container logs AND service logs separately.
</execution_in_containers>

<volume_and_data>
Volumes survive container removal. Removing a container does NOT delete data. Named volumes and bind mounts persist independently. Trap: deleting a container leaves orphaned volumes consuming storage. If data loss is possible, the script requires explicit `--force-delete-volumes` or will refuse the operation.
</volume_and_data>

<network_isolation>
Containers joined to custom networks cannot reach containers on the default bridge directly. Host mode bypasses isolation entirely. Overlay networks require swarm mode. Script abstracts network selection.
</network_isolation>

<logging_and_events>
Container logs are served by the log driver (json-file default). Large logs consume disk or are dropped depending on driver. `docker logs` follows running output; logs from exited containers may be truncated. Use `docker logs --tail=N --since=` for bounded queries.
</logging_and_events>

<registry_and_pulls>
`docker pull` fetches from registry (Docker Hub default, can be overridden). Pulling fails cleanly if the image does not exist; building fails if dependencies are missing. Pushing requires authentication.
</registry_and_pulls>
