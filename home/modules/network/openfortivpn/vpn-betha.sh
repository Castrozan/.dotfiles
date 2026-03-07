#!/usr/bin/env bash
# vpn-betha - Connect to Betha VPN via SAML
# Uses openfortivpn with SAML authentication for FortiGate VPN

export PATH="@openfortivpn@/bin:@procps@/bin:@coreutils@/bin:@gnugrep@/bin:@xdgUtils@/bin:$PATH"

VPN_HOST="vpn-lnk1.betha.com.br"
VPN_PORT="10443"
LOG_FILE="/tmp/openfortivpn.log"
OPENFORTIVPN="@openfortivpn@/bin/openfortivpn"

case "${1:-}" in
  -s|--status)
    if pgrep -x openfortivpn > /dev/null; then
      echo "VPN is connected"
      ip addr show ppp0 2>/dev/null | grep -E "inet |state" || echo "(interface info unavailable)"
    else
      echo "VPN is not connected"
    fi
    ;;
  -d|--disconnect|--stop)
    if pgrep -x openfortivpn > /dev/null; then
      sudo pkill openfortivpn
      echo "VPN disconnected"
    else
      echo "VPN is not running"
    fi
    ;;
  -a|--attach|--foreground)
    if pgrep -x openfortivpn > /dev/null; then
      echo "VPN is already connected. Use --disconnect first."
      exit 1
    fi
    echo "Connecting to $VPN_HOST:$VPN_PORT with SAML (attached)..."
    echo "A browser window will open for authentication."
    echo ""
    sudo "$OPENFORTIVPN" "$VPN_HOST:$VPN_PORT" --saml-login
    ;;
  -l|--log|--logs)
    if [ -f "$LOG_FILE" ]; then
      tail -f "$LOG_FILE"
    else
      echo "No log file found at $LOG_FILE"
    fi
    ;;
  -h|--help)
    echo "vpn-betha - Connect to Betha VPN via SAML"
    echo ""
    echo "Usage:"
    echo "  vpn-betha              Connect and detach after tunnel is up"
    echo "  vpn-betha -a|--attach  Connect in foreground (attached)"
    echo "  vpn-betha -s|--status  Check connection status"
    echo "  vpn-betha -d|--disconnect  Disconnect VPN"
    echo "  vpn-betha -l|--log     Tail the VPN log"
    echo "  vpn-betha -h|--help    Show this help"
    ;;
  *)
    if pgrep -x openfortivpn > /dev/null; then
      echo "VPN is already connected. Use --disconnect first."
      exit 1
    fi
    echo "Connecting to $VPN_HOST:$VPN_PORT with SAML..."
    echo "A browser window will open for authentication."
    echo ""

    # Clear old log and create with proper permissions
    rm -f "$LOG_FILE" 2>/dev/null || sudo rm -f "$LOG_FILE"
    touch "$LOG_FILE"
    chmod 666 "$LOG_FILE"

    # Start openfortivpn in background
    sudo nohup "$OPENFORTIVPN" "$VPN_HOST:$VPN_PORT" --saml-login >> "$LOG_FILE" 2>&1 &
    VPN_PID=$!

    echo "Waiting for SAML server to start..."

    # Wait for SAML URL to appear in log, then open browser as user
    SAML_URL=""
    for i in $(seq 1 30); do
      if grep -q "Authenticate at" "$LOG_FILE" 2>/dev/null; then
        SAML_URL=$(grep "Authenticate at" "$LOG_FILE" | sed "s/.*Authenticate at '\([^']*\)'.*/\1/")
        break
      fi
      sleep 0.5
    done

    if [ -n "$SAML_URL" ]; then
      echo "Opening browser for SAML authentication..."
      echo "(Complete login in the browser)"
      xdg-open "$SAML_URL" >/dev/null 2>&1 &
      disown 2>/dev/null
    else
      echo "Warning: Could not detect SAML URL. Check log with --log"
    fi

    # Wait silently for tunnel
    while true; do
      if grep -q "Tunnel is up and running" "$LOG_FILE" 2>/dev/null; then
        IP=$(grep "Got addresses" "$LOG_FILE" | sed 's/.*\[\([0-9.]*\)\].*/\1/' | head -1)
        echo ""
        echo "VPN connected: $IP"
        echo "Use '--log' for logs, '--disconnect' to stop."
        exit 0
      fi
      if grep -qE "ERROR:|error:" "$LOG_FILE" 2>/dev/null; then
        echo ""
        echo "Connection failed:"
        grep -E "ERROR:|error:" "$LOG_FILE"
        exit 1
      fi
      # Check if process is still running (give it time to start)
      sleep 1
      if ! kill -0 $VPN_PID 2>/dev/null && ! pgrep -x openfortivpn > /dev/null; then
        echo ""
        echo "Connection failed. Log:"
        cat "$LOG_FILE"
        exit 1
      fi
    done
    ;;
esac
