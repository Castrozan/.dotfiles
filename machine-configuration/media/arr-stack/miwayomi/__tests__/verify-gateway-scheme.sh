#!/usr/bin/env bash

set -Eeuo pipefail

gateway_configuration_path=$1
test_configuration_path="$TMPDIR/nginx.conf"

{
	printf 'pid %s/nginx.pid; error_log stderr; events {} http { access_log off;\n' "$TMPDIR"
	sed -n '/^map $http_x_forwarded_proto /,/^}/p' "$gateway_configuration_path"
	sed -n '/^map $uri /,/^}/p' "$gateway_configuration_path"
	printf 'server { listen 127.0.0.1:14568; location / { add_header Cache-Control $miwayomi_static_cache_control always; return 200 "$miwayomi_external_scheme\\n"; } } }\n'
} >"$test_configuration_path"

nginx -t -c "$test_configuration_path"
nginx -c "$test_configuration_path"
trap 'nginx -s quit -c "$test_configuration_path" >/dev/null 2>&1 || true' EXIT

test "$(curl --fail --silent --show-error -H 'X-Forwarded-Proto: https' http://127.0.0.1:14568/)" = https
test "$(curl --fail --silent --show-error -H 'X-Forwarded-Proto: https, http' http://127.0.0.1:14568/)" = https
test "$(curl --fail --silent --show-error http://127.0.0.1:14568/)" = http
test "$(curl --fail --silent --show-error --dump-header - --output /dev/null http://127.0.0.1:14568/app.js | tr -d '\r' | sed -n 's/^Cache-Control: //p')" = "no-cache, must-revalidate"
test -z "$(curl --fail --silent --show-error --dump-header - --output /dev/null http://127.0.0.1:14568/api/v1/health | tr -d '\r' | sed -n 's/^Cache-Control: //p')"
