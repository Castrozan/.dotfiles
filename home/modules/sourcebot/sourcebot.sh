#!/usr/bin/env bash

export PATH="@docker@/bin:@coreutils@/bin:@gnugrep@/bin:$PATH"

CONTAINER_NAME="sourcebot"
DATA_DIR="@dataDir@"
PORT="3000"
IMAGE="ghcr.io/sourcebot-dev/sourcebot:latest"

case "${1:-}" in
  start|"")
    mkdir -p "$DATA_DIR"

    # Create minimal config if missing (required by sourcebot)
    if [ ! -f "$DATA_DIR/config.json" ]; then
      cat > "$DATA_DIR/config.json" << 'EOFCONFIG'
{
  "$schema": "https://raw.githubusercontent.com/sourcebot-dev/sourcebot/main/schemas/v3/index.json",
  "connections": {}
}
EOFCONFIG
      echo "Created $DATA_DIR/config.json - configure repos via web UI"
    fi

    if docker ps --format '{{.Names}}' | grep -q "^$CONTAINER_NAME$"; then
      echo "Sourcebot already running at http://localhost:$PORT"
    elif docker ps -a --format '{{.Names}}' | grep -q "^$CONTAINER_NAME$"; then
      docker start "$CONTAINER_NAME"
      echo "Sourcebot started at http://localhost:$PORT"
    else
      docker run -d \
        --name "$CONTAINER_NAME" \
        -p "$PORT:3000" \
        -v "$DATA_DIR:/data" \
        -e CONFIG_PATH=/data/config.json \
        -e SOURCEBOT_TELEMETRY_DISABLED=true \
        ${GITLAB_TOKEN:+-e GITLAB_TOKEN="$GITLAB_TOKEN"} \
        "$IMAGE"
      echo "Sourcebot created and started at http://localhost:$PORT"
    fi

    sleep 2
    xdg-open "http://localhost:$PORT" >/dev/null 2>&1 &
    ;;
  stop)
    if docker ps --format '{{.Names}}' | grep -q "^$CONTAINER_NAME$"; then
      docker stop "$CONTAINER_NAME"
      echo "Sourcebot stopped"
    else
      echo "Sourcebot is not running"
    fi
    ;;
  status|-s)
    if docker ps --format '{{.Names}}' | grep -q "^$CONTAINER_NAME$"; then
      echo "Sourcebot is running at http://localhost:$PORT"
      docker ps --filter "name=$CONTAINER_NAME" --format "Container: {{.Names}}\nStatus: {{.Status}}\nPorts: {{.Ports}}"
    else
      echo "Sourcebot is not running"
    fi
    ;;
  logs|-l)
    docker logs -f "$CONTAINER_NAME"
    ;;
  update)
    docker pull "$IMAGE"
    if docker ps -a --format '{{.Names}}' | grep -q "^$CONTAINER_NAME$"; then
      docker rm -f "$CONTAINER_NAME"
      echo "Container removed. Run 'sourcebot start' to recreate with new image."
    fi
    ;;
  rm|remove)
    if docker ps -a --format '{{.Names}}' | grep -q "^$CONTAINER_NAME$"; then
      docker rm -f "$CONTAINER_NAME"
      echo "Container removed"
    else
      echo "Container does not exist"
    fi
    ;;
  -h|--help|help)
    echo "sourcebot - On-demand code search"
    echo ""
    echo "Usage:"
    echo "  sourcebot [start]   Start Sourcebot and open browser"
    echo "  sourcebot stop      Stop Sourcebot container"
    echo "  sourcebot status    Check if running"
    echo "  sourcebot logs      Follow container logs"
    echo "  sourcebot update    Pull latest image"
    echo "  sourcebot rm        Remove container (keeps data)"
    echo ""
    echo "Data: $DATA_DIR"
    ;;
  *)
    echo "Unknown command: $1"
    echo "Run 'sourcebot --help' for usage"
    exit 1
    ;;
esac
