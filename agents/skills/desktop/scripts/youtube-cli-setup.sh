#!/usr/bin/env bash
set -Eeuo pipefail

readonly CREDENTIALS_DIR="$HOME/.config/youtube-cli"
readonly CREDENTIALS_FILE="$CREDENTIALS_DIR/credentials.json"
readonly PROJECT_PREFIX="youtube-cli"
readonly APP_NAME="YouTube CLI"

_log() { echo ":: $*" >&2; }
_error() {
	echo "!! $*" >&2
	exit 1
}

_ensure_gcloud() {
	if command -v gcloud &>/dev/null; then
		return
	fi

	if [ -f /nix/var/nix/profiles/default/etc/profile.d/nix-daemon.sh ]; then
		# shellcheck disable=SC1091
		. /nix/var/nix/profiles/default/etc/profile.d/nix-daemon.sh
	fi

	if command -v nix-shell &>/dev/null; then
		_log "gcloud not found, using nix-shell wrapper"
		readonly USE_NIX_SHELL=true
		return
	fi

	_error "gcloud CLI not found. Install google-cloud-sdk or use Nix."
}

_gcloud() {
	if [ "${USE_NIX_SHELL:-}" = "true" ]; then
		nix-shell -p google-cloud-sdk --run "gcloud $*"
	else
		gcloud "$@"
	fi
}

_ensure_logged_in() {
	local current_account
	current_account=$(_gcloud auth list --filter=status:ACTIVE --format="value(account)" 2>/dev/null || true)

	if [ -z "$current_account" ]; then
		_log "Not logged in. Opening browser for Google authentication..."
		_gcloud auth login --brief
		current_account=$(_gcloud auth list --filter=status:ACTIVE --format="value(account)" 2>/dev/null)
	fi

	_log "Authenticated as: $current_account"
	echo "$current_account"
}

_create_or_select_project() {
	local existing_projects
	existing_projects=$(_gcloud projects list --format="value(projectId)" --filter="projectId:${PROJECT_PREFIX}*" 2>/dev/null || true)

	if [ -n "$existing_projects" ]; then
		local project_id
		project_id=$(echo "$existing_projects" | head -1)
		_log "Found existing project: $project_id"
		echo "$project_id"
		return
	fi

	local random_suffix
	random_suffix=$(head -c 4 /dev/urandom | od -An -tx1 | tr -d ' \n')
	local project_id="${PROJECT_PREFIX}-${random_suffix}"

	_log "Creating project: $project_id"
	_gcloud projects create "$project_id" --name="$APP_NAME" --set-as-default 2>&1 | grep -v "^$" >&2 || true

	sleep 3
	echo "$project_id"
}

_enable_youtube_api() {
	local project_id="$1"
	_log "Enabling YouTube Data API v3..."
	_gcloud services enable youtube.googleapis.com --project="$project_id" 2>&1 | grep -v "^$" >&2 || true
}

# shellcheck source=youtube-cli-setup-oauth-credentials.sh
source "$(dirname "$0")/youtube-cli-setup-oauth-credentials.sh"

_test_youtube_auth() {
	_log "Testing YouTube API authentication..."
	_log "This will open a browser for you to authorize YouTube access."
	youtube-cli playlists 2>&1 | head -5 && _log "YouTube API working!" || _log "Run 'youtube-cli playlists' to complete authorization."
}

main() {
	_log "YouTube CLI Setup"
	_log "================="
	_log ""

	if [ -f "$CREDENTIALS_FILE" ]; then
		_log "Credentials already exist at $CREDENTIALS_FILE"
		read -rp "Overwrite? [y/N] " overwrite
		if [[ ! "$overwrite" =~ ^[yY] ]]; then
			_log "Keeping existing credentials."
			_test_youtube_auth
			return
		fi
	fi

	_ensure_gcloud

	local email
	email=$(_ensure_logged_in)

	local project_id
	project_id=$(_create_or_select_project)

	_gcloud config set project "$project_id" 2>/dev/null || true

	_enable_youtube_api "$project_id"

	local brand_name
	brand_name=$(_configure_oauth_consent_screen "$project_id" "$email")

	_create_oauth_credentials "$project_id" "$brand_name"

	if [ -f "$CREDENTIALS_FILE" ]; then
		_log ""
		_log "Setup complete! Credentials at: $CREDENTIALS_FILE"
		_log ""
		_test_youtube_auth
	fi
}

main "$@"
