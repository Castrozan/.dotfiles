#!/usr/bin/env bash

cursor() {
	command cursor "$@" >/dev/null 2>&1 &
}

cu() {
	if [ $# -eq 0 ]; then
		cursor .
	else
		cursor "$@"
	fi
}
