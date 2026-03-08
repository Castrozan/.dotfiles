#!/usr/bin/env bats

setup() {
	if ! curl -sf http://localhost:9867/health >/dev/null 2>&1; then
		skip "pinchtab not running"
	fi
}

@test "mcporter chrome-devtools lists available tools" {
	run timeout 15 mcporter list chrome-devtools
	[[ "$status" -eq 0 ]]
	[[ "$output" == *"navigate_page"* ]]
	[[ "$output" == *"take_screenshot"* ]]
	[[ "$output" == *"evaluate_script"* ]]
}

@test "CDP port discovery wrapper finds chrome port" {
	local chrome_port
	chrome_port=$(ss -tlnp 2>/dev/null | grep -E 'chromium|chrome|brave' | grep -o '127\.0\.0\.1:[0-9]*' | head -1 | cut -d: -f2)
	[[ -n "$chrome_port" ]]
	[[ "$chrome_port" =~ ^[0-9]+$ ]]
	run timeout 5 curl -sf "http://127.0.0.1:$chrome_port/json/version"
	[[ "$status" -eq 0 ]]
}

@test "navigate_page navigates to URL" {
	run timeout 15 mcporter call chrome-devtools.navigate_page type=url url=https://example.com
	[[ "$status" -eq 0 ]]
	[[ "$output" == *"Successfully navigated"* ]]
}

@test "evaluate_script returns javascript result" {
	run timeout 15 mcporter call chrome-devtools.evaluate_script function="() => document.title"
	[[ "$status" -eq 0 ]]
	[[ "$output" == *"Example Domain"* ]]
}

@test "take_snapshot returns accessibility tree with UIDs" {
	run timeout 15 mcporter call chrome-devtools.take_snapshot
	[[ "$status" -eq 0 ]]
	[[ "$output" == *"uid="* ]]
	[[ "$output" == *"RootWebArea"* ]]
}

@test "take_screenshot captures page" {
	run timeout 15 mcporter call chrome-devtools.take_screenshot
	[[ "$status" -eq 0 ]]
	[[ "$output" == *"screenshot"* ]]
}

@test "list_pages shows current page" {
	run timeout 15 mcporter call chrome-devtools.list_pages
	[[ "$status" -eq 0 ]]
	[[ "$output" == *"example.com"* ]]
}

@test "navigate back works" {
	run timeout 15 mcporter call chrome-devtools.navigate_page type=back
	[[ "$status" -eq 0 ]]
	[[ "$output" == *"navigated back"* ]]
}

@test "mcporter config uses CDP discovery wrapper not hardcoded port" {
	[[ ! "$(cat ~/.mcporter/mcporter.json)" == *"9222"* ]]
}
