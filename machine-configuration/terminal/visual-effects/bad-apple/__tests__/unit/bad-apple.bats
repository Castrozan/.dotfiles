#!/usr/bin/env bats

setup() {
	BAD_APPLE_SCRIPT="$(cd "$(dirname "$BATS_TEST_FILENAME")/../.." && pwd)/scripts/bad-apple"
	WRAPPER_SHELL="$BASH"
	TEMPORARY_ROOT="$(mktemp -d)"
	FAKE_BINARY_DIRECTORY="$TEMPORARY_ROOT/bin"
	FAKE_HOME_DIRECTORY="$TEMPORARY_ROOT/home"
	SINGLE_VIDEO_URL="https://www.youtube.com/watch?v=FtutLA63Cp8"
	mkdir -p "$FAKE_BINARY_DIRECTORY" "$FAKE_HOME_DIRECTORY"

	cat >"$FAKE_BINARY_DIRECTORY/tput" <<-'FAKE_TPUT'
		#!/usr/bin/env bash
		case "$1" in
		cols) echo "$FAKE_TERMINAL_COLUMNS" ;;
		lines) echo "$FAKE_TERMINAL_LINES" ;;
		esac
	FAKE_TPUT

	cat >"$FAKE_BINARY_DIRECTORY/yt-dlp" <<-'FAKE_YT_DLP'
		#!/usr/bin/env bash
		while [ "$#" -gt 0 ]; do
			if [ "$1" = "-o" ]; then
				mkdir -p "$(dirname "$2")"
				printf 'fake video' >"$2"
				exit 0
			fi
			shift
		done
		exit 1
	FAKE_YT_DLP

	cat >"$FAKE_BINARY_DIRECTORY/ffmpeg" <<-'FAKE_FFMPEG'
		#!/usr/bin/env bash
		for argument in "$@"; do
			case "$argument" in
			*frame_%04d.png)
				printf 'fake frame' >"${argument/\%04d/0001}"
				exit 0
				;;
			esac
		done
		exit 1
	FAKE_FFMPEG

	cat >"$FAKE_BINARY_DIRECTORY/chafa" <<-'FAKE_CHAFA'
		#!/usr/bin/env bash
		echo "fake-braille-row"
	FAKE_CHAFA

	cat >"$FAKE_BINARY_DIRECTORY/gawk" <<-'FAKE_GAWK'
		#!/usr/bin/env bash
		exec awk "$@"
	FAKE_GAWK

	cat >"$FAKE_BINARY_DIRECTORY/sleep" <<-'FAKE_SLEEP'
		#!/usr/bin/env bash
		kill "$PPID"
	FAKE_SLEEP

	chmod +x "$FAKE_BINARY_DIRECTORY"/*
}

teardown() {
	rm -rf "$TEMPORARY_ROOT"
}

run_bad_apple() {
	run env -i \
		HOME="$FAKE_HOME_DIRECTORY" \
		PATH="$FAKE_BINARY_DIRECTORY:$PATH" \
		FAKE_TERMINAL_COLUMNS=200 \
		FAKE_TERMINAL_LINES=60 \
		"$@" \
		"$WRAPPER_SHELL" "$BAD_APPLE_SCRIPT"
}

@test "plays the configured url and caches its frames under the home cache directory" {
	run_bad_apple BAD_APPLE_VIDEO_URLS="$SINGLE_VIDEO_URL"
	[[ "$output" == *"Downloading video (FtutLA63Cp8)..."* ]]
	[[ "$output" == *"Done! Frames cached at $FAKE_HOME_DIRECTORY/.cache/bad-apple/FtutLA63Cp8/frames-200x60-fps30-delta1-braille"* ]]
}

@test "roots the frame cache at XDG_CACHE_HOME when it is set" {
	run_bad_apple \
		BAD_APPLE_VIDEO_URLS="$SINGLE_VIDEO_URL" \
		XDG_CACHE_HOME="$TEMPORARY_ROOT/xdg"
	[[ "$output" == *"Done! Frames cached at $TEMPORARY_ROOT/xdg/bad-apple/FtutLA63Cp8/frames-200x60-fps30-delta1-braille"* ]]
}

@test "renders the full terminal at thirty frames per second outside wezterm" {
	run_bad_apple BAD_APPLE_VIDEO_URLS="$SINGLE_VIDEO_URL"
	[[ "$output" == *"Generating delta frames for 200x60 at 30fps..."* ]]
}

@test "clamps to 140x45 at fifteen frames per second inside wezterm" {
	run_bad_apple BAD_APPLE_VIDEO_URLS="$SINGLE_VIDEO_URL" WEZTERM_PANE=3
	[[ "$output" == *"Generating delta frames for 140x45 at 15fps..."* ]]
}

@test "BAD_APPLE_FPS overrides both the wezterm and non-wezterm frame rate defaults" {
	run_bad_apple BAD_APPLE_VIDEO_URLS="$SINGLE_VIDEO_URL" BAD_APPLE_FPS=7
	[[ "$output" == *"Generating delta frames for 200x60 at 7fps..."* ]]

	run_bad_apple BAD_APPLE_VIDEO_URLS="$SINGLE_VIDEO_URL" WEZTERM_PANE=3 BAD_APPLE_FPS=7
	[[ "$output" == *"Generating delta frames for 140x45 at 7fps..."* ]]
}

@test "BAD_APPLE_MAX_COLS overrides both the wezterm and non-wezterm width ceilings" {
	run_bad_apple BAD_APPLE_VIDEO_URLS="$SINGLE_VIDEO_URL" BAD_APPLE_MAX_COLS=80
	[[ "$output" == *"Generating delta frames for 80x60 at 30fps..."* ]]

	run_bad_apple BAD_APPLE_VIDEO_URLS="$SINGLE_VIDEO_URL" WEZTERM_PANE=3 BAD_APPLE_MAX_COLS=180
	[[ "$output" == *"Generating delta frames for 180x45 at 15fps..."* ]]
}

@test "selects across the whole configured url list rather than a fixed entry" {
	local configuredUrls
	configuredUrls="https://www.youtube.com/watch?v=FtutLA63Cp8
https://www.youtube.com/watch?v=CqaAs_3azSs
https://www.youtube.com/watch?v=lX44CAz-JhU"
	local observedVideoIds=""
	local attempt
	local selectedVideoId
	for attempt in $(seq 1 12); do
		run_bad_apple \
			HOME="$TEMPORARY_ROOT/home-$attempt" \
			BAD_APPLE_VIDEO_URLS="$configuredUrls"
		selectedVideoId="$(echo "$output" | sed -n 's/^Downloading video (\(.*\))\.\.\.$/\1/p' | head -1)"
		[ -n "$selectedVideoId" ]
		[[ "$configuredUrls" == *"v=$selectedVideoId"* ]]
		observedVideoIds="$observedVideoIds$selectedVideoId
"
	done
	[ "$(echo "$observedVideoIds" | sort -u | grep -c .)" -gt 1 ]
}
