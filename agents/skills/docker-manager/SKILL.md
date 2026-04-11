---
name: docker-manager
description: Manage Docker containers, images, volumes, and networks. Execute commands in containers, inspect state, view logs, build images. Use docker-manager script for safe operations.
---

<script_location>
  Primary logic lives in scripts/docker-manager. Invoke as a helper to automate Docker workflows safely without exposing raw docker commands. Script manages error handling, output parsing, and container lifecycle constraints that raw docker CLI exposes unsafely.
</script_location>

<safety_boundaries>
  Script runs docker commands via a curated interface. Do not bypass it with raw docker calls even if it seems faster — the script enforces ordering (stop before remove), prevents data loss (volume backup before delete), and surfaces errors the daemon hides. Common trap: docker rm succeeds on stopped containers; docker rmi fails if container still references image — script handles this cascade.
</safety_boundaries>

<container_state>
  Containers have multiple states (created, running, paused, stopped, exiting, dead). Status checks are point-in-time snapshots — a container running at inspection time may crash milliseconds later. When scripting multi-step workflows (start, wait for healthcheck, then exec), insert actual waits, not just state queries. "Container is running" does not mean "ready to accept traffic."
</container_state>

<execution_in_containers>
  docker exec works only on running containers. If exec must happen regardless of state, use the script's container-ensure-running helper or wrap the exec with explicit start logic. Exit codes from exec are reliable; container logs are not (buffering, log driver limits). When debugging failed execs, check container logs AND service logs separately.
</execution_in_containers>

<volume_and_data>
  Volumes survive container removal. Removing a container does NOT delete data. Named volumes and bind mounts persist independently. Trap: deleting a container leaves orphaned volumes consuming storage. Verify current cleanup strategy by checking scripts/docker-manager for prune behavior. If data loss is possible, the script requires explicit --force-delete-volumes or will refuse the operation.
</volume_and_data>

<image_dependency>
  A running or stopped container holds a reference to its image. Removing the image fails until the container is removed. Image removal is idempotent only if the tag is unused; rebuilding with the same tag orphans the old image but doesn't remove it. Dangling images accumulate. Script's image-cleanup handles this; verify current prune policy before using it.
</image_dependency>

<network_isolation>
  Containers joined to custom networks cannot reach containers on the default bridge directly. Host mode bypasses isolation entirely. Overlay networks require swarm mode. Script abstracts network selection; inspect usage in workflow context to understand connectivity model.
</network_isolation>

<logging_and_events>
  Container logs are served by the log driver (json-file default, others available). Large logs consume disk or are dropped depending on driver. docker logs follows running output; logs from exited containers may be truncated. Use docker logs --tail=N --since= for bounded queries. Script exposes log retrieval; verify truncation behavior matches your retention needs.
</logging_and_events>

<registry_and_pulls>
  docker pull fetches from registry (Docker Hub default, can be overridden). Pulling fails cleanly if the image does not exist; building fails if dependencies are missing. Pushing requires authentication. Script handles registry selection and auth context; check scripts/docker-manager for current credential defaults before assuming unauthenticated pushes work.
</registry_and_pulls>
