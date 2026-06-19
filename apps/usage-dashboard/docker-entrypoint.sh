#!/bin/sh
set -eu

export PORT="${PORT:-8080}"

envsubst '${PORT}' </etc/nginx/nginx.conf.template >/etc/nginx/nginx.conf

exec nginx -g 'daemon off;'
