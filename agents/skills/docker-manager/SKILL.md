---
name: docker-manager
description: Manage Docker containers, images, volumes, and networks. Execute commands in containers, inspect state, view logs, build images. Use docker-manager script for safe operations.
---

<invoke>
Run `docker-manager --help` to list subcommands. Each operation wraps Docker CLI with state verification, error detection, and safety checks. Read specific subcommand help for exact flags and syntax.
</invoke>

<traps>
<state_transitions>
Containers transition through states asynchronously: running → stopping (SIGTERM grace period, default 10s) → stopped. Checks immediately after stop commands may return "running" or "exited" unpredictably if racing with signal delivery. Always poll with brief sleeps or use --wait flags when operation ordering depends on final state. Force-kill (--force-kill) skips grace period, losing in-flight data in buffered processes and leaving zombie states.
</state_transitions>

<cleanup_after_errors>
Failed container operations leave orphaned containers, volumes, and dangling image layers. After errors, verify actual state with `docker ps -a`, `docker volume ls`, `docker images`. Dangling volumes and intermediate images accumulate silently and consume disk space. `docker volume prune` and `docker image prune` clean unused resources, but only after confirming no running or stopped container depends on them — pruning can break subsequent runs if shared layers are unexpectedly removed.
</cleanup_after_errors>

<permission_model>
Docker socket requires membership in docker group OR sudo execution. Verify permission with `docker ps` before proceeding. Containers run with host UID by default (root 0 unless --user specified). Bind-mounted host files retain host ownership; container user may lack write permission even with 777 directory mode. Use explicit --user flag and test file permissions when writes matter.
</permission_model>

<image_caching_and_tags>
Pull operations cache layers; identical image can have multiple tags. `docker images` shows all tags, not unique images. Build cache persists across rebuilds — changing only final RUN layers reuses earlier ones, making builds fast but introducing stale-cache bugs. Force fresh build with --no-cache at cost of extended build time. Unused images consume disk; `docker image prune` removes only untagged intermediate images, not all unused ones.
</image_caching_and_tags>

<network_isolation>
Containers on default bridge network cannot resolve each other by hostname. Use --network with explicit custom network name or deprecated --link for DNS resolution between containers. Port mapping (-p) binds container port to host port; collision silently fails during start — verify binding with `docker port` after start. Host mode (--network host) bypasses Docker's network isolation, exposing container ports directly to host and losing all port isolation.
</network_isolation>

<volume_mount_traps>
Bind mounts create missing host paths automatically, often with wrong ownership. Named volumes are managed by Docker; bind mounts are host-managed. Container writes to unmounted paths layer into the container's writable layer (copy-on-write), which disappears on `docker rm`. Volume must exist before mount or data persists in wrong location. Paths for bind mounts must be absolute or explicitly relative to a known location; relative paths break under working directory changes.
</volume_mount_traps>

<exec_in_stopped_containers>
`docker exec` silently fails on stopped containers with "Container is not running" error. Similarly, `docker logs` works on stopped containers but shows old logs, not current process state. Always verify container is running (`docker ps` without -a) before assuming `docker exec` will reach a responsive process.
</exec_in_stopped_containers>

<resource_limits_not_retroactive>
Memory and CPU limits set at container start time. Changing limits requires stop → remove → run with new flags. Limits prevent new allocations beyond the threshold but do not reclaim already-allocated memory. OOM killer terminates container if usage exceeds limit, but behavior is daemon-configurable and can silently allow overallocation if misconfigured. Verify limits took effect with `docker stats` — do not assume enforcement.
</resource_limits_not_retroactive>

<healthcheck_is_metadata>
Dockerfile HEALTHCHECK sets status metadata only; Docker does not auto-restart on failure. Health status is visible to orchestration layers (Docker Swarm, Kubernetes) but is inert in standalone Docker. Container continues running even if HEALTHCHECK reports unhealthy. Implement explicit restart logic outside Docker if health-based restart is required.
</healthcheck_is_metadata>

<filesystem_sync_not_guaranteed>
Volume snapshot state is not point-in-time consistent unless writes are paused. Database containers should use named volumes (not layers), and backups should stop the container or pause writes during snapshot. Restarting Docker daemon without stopping containers leaves Docker state inconsistent with actual container processes.
</filesystem_sync_not_guaranteed>

<compose_file_location>
Docker Compose reads compose.yaml or docker-compose.yaml from current directory. Changing directory or filename changes which file is loaded. Use explicit -f flag to specify file path. Environment substitution in compose files uses host $VAR or .env file; Docker does not inherit container environment.
</compose_file_location>

<exit_code_semantics>
Exit code 0 from `docker run` indicates the container process exited with code 0, NOT that the command succeeded. Check container logs (`docker logs`) for actual process output and verify expected behavior — exit code 0 does not guarantee the process did what you intended.
</exit_code_semantics>

<registry_auth_host_specific>
`docker login` caches credentials in ~/.docker/config.json on the host. Credentials are host-specific and do not transfer to other machines. Private registry operations require prior login; `docker push` fails with 401 if credentials are stale or missing. Registry URL in image name (registry.example.com/repo/image) determines which credentials are used.
</registry_auth_host_specific>

<volume_driver_installation>
Default volume driver is local (host filesystem). Custom drivers (nfs, iscsi, plugins) require separate installation and configuration. Using a missing driver silently fails during container start with network or path errors. Verify driver availability with `docker volume inspect` before relying on it.
</volume_driver_installation>
</traps>

<ordering_constraints>
Network and volume creation must precede container creation if using --network name or -v named-volume:path. Multi-stage builds require Docker 17.05+. Building images from Dockerfile with custom BuildKit requires BuildKit daemon running. Pushing to private registry requires successful `docker login` before `docker push`.
</ordering_constraints>

<verification_patterns>
Always verify preconditions before acting: container exists before start, image exists before run, port available before binding, volume mounted before write. Use explicit state checks (docker ps, docker images, docker volume ls) rather than assuming state. Operations can fail gracefully but also can silently produce wrong results. Test that expected side effects occurred, not just that the command returned success.
</verification_patterns>

<common_subcommands>
<run_container>
docker-manager run --name NAME --image IMAGE [--publish PORT:PORT] [--volume VOLUME:PATH] [--env VAR=VALUE] [--command COMMAND]. Creates and starts a new container with isolation and resource limits.
</run_container>

<execute_in_container>
docker-manager exec --name NAME [--user USER] COMMAND. Execute command inside running container. Fails if container stopped.
</execute_in_container>

<view_logs>
docker-manager logs --name NAME [--follow] [--tail N]. Stream or tail container logs. Works on stopped containers but shows old logs, not current state.
</view_logs>

<stop_container>
docker-manager stop --name NAME [--timeout SECONDS]. Send SIGTERM, wait grace period, then SIGKILL. Use --force-kill to skip grace period.
</stop_container>

<remove_container>
docker-manager remove --name NAME [--force]. Delete stopped container. Use --force to kill before removing.
</remove_container>

<list_containers>
docker-manager list [--all]. Show running containers (omit --all to exclude stopped). Verify container exists before operating on it.
</list_containers>

<build_image>
docker-manager build --name NAME [--dockerfile PATH] [--no-cache] CONTEXT. Build image from Dockerfile. Cache persists across builds — use --no-cache for fresh build.
</build_image>

<push_image>
docker-manager push --image IMAGE [--registry REGISTRY]. Push image to registry. Requires `docker login REGISTRY` before pushing.
</push_image>

<create_volume>
docker-manager volume-create --name NAME. Create named volume managed by Docker. Use for persistent data, not temporary layers.
</create_volume>

<create_network>
docker-manager network-create --name NAME [--driver DRIVER]. Create custom network for container-to-container DNS resolution. Default bridge does not support hostname resolution.
</create_network>
</common_subcommands>

</traps>
