readonly FORTICLIENT_REAL="/opt/forticlient/gui/FortiClient.real"

main() {
	local fabricagent_url="${1:-}"

	if [[ -z "${fabricagent_url}" ]]; then
		echo >&2 "Usage: forticlient-auth-callback 'fabricagent://ems/onboarding?username=...&auth_token=...'"
		exit 1
	fi

	if [[ "${fabricagent_url}" != fabricagent://* ]]; then
		echo >&2 "Error: URL must start with fabricagent://"
		exit 1
	fi

	"${FORTICLIENT_REAL}" "${fabricagent_url}" >/dev/null 2>&1
	echo "Auth callback sent to FortiClient."
}

main "$@"
