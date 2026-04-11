# Docker Manager - Agent Prompts

## Core Pattern: Use the Script, Never Raw Docker

When working with containers, always delegate to `docker-manager` script. It handles:
- **Ordering safety**: Stop before remove, avoid cascade failures
- **Data safety**: Warn before volume deletion, optional backups
- **Error handling**: Clear errors when preconditions fail (e.g., exec on stopped container)
- **Output parsing**: Reliable JSON for scripting, human-readable tables for inspection

**Bad:**
```bash
docker rm my-container
docker rmi my-image
```

**Good:**
```bash
docker-manager remove my-container
docker-manager remove-image my-image
```

---

## Pattern: Container Lifecycle

### Start with Validation
Always check container state before operations:

```bash
# First: List what's running
docker-manager list

# Inspect before making changes
docker-manager inspect my-app

# Then perform safe operations
docker-manager stop my-app
docker-manager remove my-app --remove-volumes
```

### Waiting for Readiness
State transitions take time. Don't assume "running" means "ready":

```bash
# ✓ Wait for running state AND healthcheck
docker-manager start postgres --wait-running 30
docker-manager healthcheck postgres --wait 60

# ✓ Then verify connectivity
docker-manager exec postgres psql -U user -c "SELECT 1"

# ✗ Don't skip the wait
# docker-manager start postgres && docker-manager exec postgres ...
```

### Cleanup Pattern
Always remove unused resources:

```bash
# Before stopping, identify what will be lost
docker-manager inspect-volume my-data

# Backup before deletion (optional)
docker-manager remove-volume my-data --backup-to ./backups/my-data.tar.gz

# Or just remove (orphaned volumes remain, use cleanup)
docker-manager remove my-old-app --remove-volumes

# Periodically cleanup dangling images
docker-manager cleanup-images --dry-run
docker-manager cleanup-images
```

---

## Pattern: Debugging

### Logs and Events
Logs are point-in-time, may be truncated:

```bash
# Recent logs (last 50 lines)
docker-manager logs my-app --tail=50

# Stream in real-time
docker-manager logs my-app --follow

# Logs from last 5 minutes
docker-manager logs my-app --since=5m

# For hung processes, also check host/docker events
docker-manager events --filter type=container --since=10m
```

### Exec for Debugging
Only works on running containers:

```bash
# First ensure it's running
docker-manager start my-app

# Then execute
docker-manager exec my-app curl -s http://localhost:3000/health

# Capture output for analysis
docker-manager exec my-app ps aux > process-list.txt
docker-manager exec my-app netstat -tln > listening-ports.txt
```

### System Stats
For performance diagnosis:

```bash
# Single snapshot
docker-manager stats --interval 1

# Per-container (watch mode, Ctrl-C to exit)
docker-manager stats --container my-app
```

---

## Pattern: Image Management

### Building with Args
Pass environment-specific values at build time:

```bash
docker-manager build . \
  --tag myservice:v1.0.0 \
  --build-arg NODE_ENV=production \
  --build-arg API_URL=https://api.example.com
```

### Pushing Requires Auth
Registry login happens outside this script:

```bash
# Verify auth setup first
echo $DOCKER_CONFIG  # Should be set to auth directory

# Push to Docker Hub (default)
docker-manager push myservice:v1.0.0

# Push to private registry
docker-manager push myregistry.com/myservice:v1.0.0 --registry myregistry.com
```

### Image Cleanup
Dangling images don't consume pull quota but waste disk:

```bash
# Find dangling (orphaned by rebuilds)
docker-manager images --filter dangling=true

# Safe removal (tells you what's unused)
docker-manager cleanup-images --dry-run
docker-manager cleanup-images
```

---

## Pattern: Volumes and Persistence

### Volume State Survives Container Removal
**Trap:** Removing a container doesn't delete its data.

```bash
# Volume info before removal
docker-manager inspect-volume my-data

# List containers using it
docker-manager list | grep my-data  # Still referenced by stopped containers

# Remove container
docker-manager remove my-app

# Volume still exists!
docker-manager inspect-volume my-data  # Exists but orphaned

# Choose: backup or delete
docker-manager remove-volume my-data --backup-to ./backups/
```

### Named Volumes vs Bind Mounts
Named volumes are managed by Docker, bind mounts use host paths:

```bash
# Named volume (isolated, managed by Docker)
docker volume create my-data

# Bind mount (direct host path, use for development)
# Must be specified in docker run/compose, not managed here
```

---

## Pattern: Networks and Isolation

### Custom Networks Isolate
Default bridge doesn't connect containers by DNS name:

```bash
# Create custom network for app cluster
docker-manager networks  # Check existing

# Containers on custom network can reach each other by name:
# docker run --network mynet --name app1 ...
# docker run --network mynet --name app2 ...
# app1 can curl http://app2:3000
```

---

## Error Handling Rules

### Container Not Running
Exec fails cleanly on stopped containers:

```bash
# ✓ Script checks and fails with clear error
docker-manager exec my-app curl http://localhost:3000
# Error: Container not running. Start it first.

# ✓ Operator's job to start and retry
docker-manager start my-app
docker-manager exec my-app curl http://localhost:3000
```

### Image Dependency
Can't remove image while containers reference it:

```bash
# ✓ Script checks and fails
docker-manager remove-image myimage:v1
# Error: Container(s) reference this image: abc123
# Use --force or remove containers first.

# ✓ Remove containers or use --force
docker-manager remove my-container
docker-manager remove-image myimage:v1

# OR (dangerous, only if really sure)
docker-manager remove-image myimage:v1 --force
```

### Volume Dependencies
Named volumes don't auto-cleanup:

```bash
# Script warns before deletion
docker-manager remove-volume my-data
# Removes immediately (no containers reference it)

# If containers still reference it, script shows warning:
# WARNING: Containers still using this volume: abc123
# Use --force or remove containers first
```

---

## Workflow Example: Redeploy Service

```bash
#!/bin/bash
set -e

SERVICE="my-api"
IMAGE="myregistry.com/$SERVICE:v2.0"

echo "=== Building new image ==="
docker-manager build . --tag "$IMAGE" --build-arg ENV=prod

echo "=== Pushing to registry ==="
docker-manager push "$IMAGE"

echo "=== Stopping old container ==="
docker-manager stop "$SERVICE"

echo "=== Removing old container and volumes ==="
docker-manager remove "$SERVICE" --remove-volumes

echo "=== Starting new container ==="
# Requires docker run or compose; docker-manager only starts existing containers
docker run -d --name "$SERVICE" \
  -e DATABASE_URL=postgres://... \
  -p 3000:3000 \
  "$IMAGE"

echo "=== Waiting for service ==="
docker-manager start "$SERVICE" --wait-running 30
docker-manager healthcheck "$SERVICE" --wait 60

echo "=== Verifying ==="
docker-manager logs "$SERVICE" --tail=20
docker-manager exec "$SERVICE" curl http://localhost:3000/health

echo "=== Done ==="
```

---

## When NOT to Use docker-manager

- **Creating new containers from scratch** → Use `docker run` directly or docker-compose
- **Orchestration (swarm/k8s)** → Use swarm/kubectl commands
- **Multi-container apps** → Use docker-compose (docker-manager works on single containers)
- **Registry auth setup** → Use `docker login` directly

The script assumes containers already exist. For initial creation, use native Docker or docker-compose, then manage with this script.
