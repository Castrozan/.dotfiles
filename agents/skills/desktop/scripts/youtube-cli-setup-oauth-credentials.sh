# shellcheck shell=bash

_configure_oauth_consent_screen() {
	local project_id="$1"
	local email="$2"

	_log "Configuring OAuth consent screen..."

	local access_token
	access_token=$(_gcloud auth print-access-token 2>/dev/null)

	local existing_brand
	existing_brand=$(curl -s -H "Authorization: Bearer $access_token" \
		"https://iap.googleapis.com/v1/projects/${project_id}/brands" 2>/dev/null |
		python3 -c "import sys,json; brands=json.load(sys.stdin).get('brands',[]); print(brands[0]['name'] if brands else '')" 2>/dev/null || true)

	if [ -n "$existing_brand" ]; then
		_log "OAuth consent screen already configured"
		echo "$existing_brand"
		return
	fi

	local project_number
	project_number=$(_gcloud projects describe "$project_id" --format="value(projectNumber)" 2>/dev/null)

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

	local project_number
	project_number=$(_gcloud projects describe "$project_id" --format="value(projectNumber)" 2>/dev/null)

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
	cat >"$CREDENTIALS_FILE" <<EOF
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
