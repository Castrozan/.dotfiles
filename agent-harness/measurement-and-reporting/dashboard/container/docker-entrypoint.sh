#!/bin/sh
set -eu

export PORT="${PORT:-8080}"

envsubst "\${PORT}" </etc/nginx/nginx.conf.template >/tmp/usage-dashboard-nginx.conf

exec nginx -c /tmp/usage-dashboard-nginx.conf -g 'daemon off;'
