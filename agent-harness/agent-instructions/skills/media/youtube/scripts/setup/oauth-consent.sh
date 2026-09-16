#!/usr/bin/env bash
_configure_oauth_consent_screen() {
	local project_id="$1"
	local email="$2"

	_log "Configuring OAuth consent screen..."

	local access_token
	access_token=$(_gcloud auth print-access-token 2>/dev/null)

	# Check if brand already exists
	local existing_brand
	existing_brand=$(curl -s -H "Authorization: Bearer $access_token" \
		"https://iap.googleapis.com/v1/projects/${project_id}/brands" 2>/dev/null |
		python3 -c "import sys,json; brands=json.load(sys.stdin).get('brands',[]); print(brands[0]['name'] if brands else '')" 2>/dev/null || true)

	if [[ -n "$existing_brand" ]]; then
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

	if [[ -z "$brand_name" ]]; then
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
	return
}
