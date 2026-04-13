#!/usr/bin/env bash
set -Eeuo pipefail

readonly CREDENTIALS_DIR="$HOME/.config/youtube-cli"
readonly CREDENTIALS_FILE="$CREDENTIALS_DIR/credentials.json"
readonly PROJECT_PREFIX="youtube-cli"
readonly APP_NAME="YouTube CLI"

_log() { echo ":: $*" >&2; }
_error() { echo "!! $*" >&2; exit 1; }

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

  # Wait for project to be ready
  sleep 3
  echo "$project_id"
}

_enable_youtube_api() {
  local project_id="$1"
  _log "Enabling YouTube Data API v3..."
  _gcloud services enable youtube.googleapis.com --project="$project_id" 2>&1 | grep -v "^$" >&2 || true
}

_configure_oauth_consent_screen() {
  local project_id="$1"
  local email="$2"

  _log "Configuring OAuth consent screen..."

  local access_token
  access_token=$(_gcloud auth print-access-token 2>/dev/null)

  # Check if brand already exists
  local existing_brand
  existing_brand=$(curl -s -H "Authorization: Bearer $access_token" \
    "https://iap.googleapis.com/v1/projects/${project_id}/brands" 2>/dev/null | \
    python3 -c "import sys,json; brands=json.load(sys.stdin).get('brands',[]); print(brands[0]['name'] if brands else '')" 2>/dev/null || true)

  if [ -n "$existing_brand" ]; then
    _log "OAuth consent screen already configured"
    echo "$existing_brand"
    return
  fi

  # Get project number
  local project_number
  project_number=$(_gcloud projects describe "$project_id" --format="value(projectNumber)" 2>/dev/null)

  # Create OAuth brand (consent screen)
  local brand_response
  brand_response=$(curl -s -X POST \
    -H "Authorization: Bearer $access_token" \
    -H "Content-Type: application/json" \
    -d "{\"applicationTitle\": \"${APP_NAME}\", \"supportEmail\": \"${email}\"}" \
    "https://iap.googleapis.com/v1/projects/${project_number}/brands" 2>/dev/null)

  local brand_name
  brand_name=$(echo "$brand_response" | python3 -c "import sys,json; print(json.load(sys.stdin).get('name',''))" 2>/dev/null || true)

  if [ -z "$brand_name" ]; then
    _log "Warning: Could not create consent screen via API. Response: $brand_response"
    _log "Falling back to manual consent screen setup..."
    _setup_consent_screen_manually "$project_id"
    brand_name="manual"
  fi

  echo "$brand_name"
}

_setup_consent_screen_manually() {
  local project_id="$1"
  local consent_url="https://console.cloud.google.com/apis/credentials/consent?project=${project_id}"
  _log "Opening consent screen setup at:"
  _log "  $consent_url"
  _log ""
  _log "Quick steps:"
  _log "  1. Select 'External' → Create"
  _log "  2. App name: YouTube CLI"
  _log "  3. User support email: your email"
  _log "  4. Developer contact: your email"
  _log "  5. Save and Continue (skip scopes, test users)"
  _log ""
  xdg-open "$consent_url" 2>/dev/null || open "$consent_url" 2>/dev/null || true
  read -rp "Press Enter when done..."
}

_create_oauth_credentials() {
  local project_id="$1"
  local brand_name="$2"

  _log "Creating OAuth2 client credentials..."

  local access_token
  access_token=$(_gcloud auth print-access-token 2>/dev/null)

  if [ "$brand_name" != "manual" ]; then
    # Try creating via IAP API (works for internal brands)
    local client_response
    client_response=$(curl -s -X POST \
      -H "Authorization: Bearer $access_token" \
      -H "Content-Type: application/json" \
      -d "{\"displayName\": \"${APP_NAME} Desktop\"}" \
      "https://iap.googleapis.com/v1/${brand_name}/identityAwareProxyClients" 2>/dev/null)

    local client_id client_secret
    client_id=$(echo "$client_response" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('name','').split('/')[-1])" 2>/dev/null || true)
    client_secret=$(echo "$client_response" | python3 -c "import sys,json; print(json.load(sys.stdin).get('secret',''))" 2>/dev/null || true)

    if [ -n "$client_id" ] && [ -n "$client_secret" ] && [ "$client_id" != "" ]; then
      _write_credentials "$client_id" "$client_secret"
      return
    fi

    _log "IAP client creation didn't return expected format. Trying REST API..."
  fi

  # Fallback: use the OAuth2 REST API to create a Desktop client
  local project_number
  project_number=$(_gcloud projects describe "$project_id" --format="value(projectNumber)" 2>/dev/null)

  # Try creating via the Cloud Console internal API
  local create_response
  create_response=$(curl -s -X POST \
    -H "Authorization: Bearer $access_token" \
    -H "Content-Type: application/json" \
    -d '{
      "client_id": "",
      "client_type": "INSTALLED_APP",
      "display_name": "'"${APP_NAME}"' Desktop",
      "installed_app_type": "DESKTOP"
    }' \
    "https://content-clientauthconfig.googleapis.com/v1/projects/${project_number}/clients" 2>/dev/null)

  local created_client_id created_client_secret
  created_client_id=$(echo "$create_response" | python3 -c "import sys,json; print(json.load(sys.stdin).get('clientId',''))" 2>/dev/null || true)
  created_client_secret=$(echo "$create_response" | python3 -c "import sys,json; print(json.load(sys.stdin).get('clientSecret',''))" 2>/dev/null || true)

  if [ -n "$created_client_id" ] && [ -n "$created_client_secret" ]; then
    _write_credentials "$created_client_id" "$created_client_secret"
    return
  fi

  _log "API creation failed. Response: $create_response"
  _log ""
  _create_credentials_via_browser "$project_id"
}

_create_credentials_via_browser() {
  local project_id="$1"
  local credentials_url="https://console.cloud.google.com/apis/credentials/oauthclient?project=${project_id}"

  _log "Opening credentials page directly (skip console navigation):"
  _log "  $credentials_url"
  _log ""
  _log "  1. Application type: Desktop app"
  _log "  2. Name: YouTube CLI Desktop"
  _log "  3. Click Create"
  _log "  4. Click 'Download JSON'"
  _log "  5. Save to: $CREDENTIALS_FILE"
  _log ""
  xdg-open "$credentials_url" 2>/dev/null || open "$credentials_url" 2>/dev/null || true
  read -rp "Press Enter after saving credentials.json..."

  if [ ! -f "$CREDENTIALS_FILE" ]; then
    _log "Credentials file not found at $CREDENTIALS_FILE"
    read -rp "Enter the path where you saved the JSON: " downloaded_path
    if [ -f "$downloaded_path" ]; then
      mkdir -p "$CREDENTIALS_DIR"
      cp "$downloaded_path" "$CREDENTIALS_FILE"
      _log "Credentials saved to $CREDENTIALS_FILE"
    else
      _error "File not found: $downloaded_path"
    fi
  fi
}

_write_credentials() {
  local client_id="$1"
  local client_secret="$2"

  mkdir -p "$CREDENTIALS_DIR"
  cat > "$CREDENTIALS_FILE" <<EOF
{
  "installed": {
    "client_id": "${client_id}",
    "client_secret": "${client_secret}",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "redirect_uris": ["http://localhost"]
  }
}
EOF
  _log "Credentials saved to $CREDENTIALS_FILE"
}

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
