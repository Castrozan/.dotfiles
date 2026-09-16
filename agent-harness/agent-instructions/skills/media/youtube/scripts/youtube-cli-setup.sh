#!/usr/bin/env bash
# shellcheck source-path=SCRIPTDIR
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

SETUP_DIRECTORY="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/setup"

# shellcheck source=setup/google-cloud-project.sh
source "$SETUP_DIRECTORY/google-cloud-project.sh"
# shellcheck source=setup/oauth-consent.sh
source "$SETUP_DIRECTORY/oauth-consent.sh"
# shellcheck source=setup/oauth-credentials.sh
source "$SETUP_DIRECTORY/oauth-credentials.sh"

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
