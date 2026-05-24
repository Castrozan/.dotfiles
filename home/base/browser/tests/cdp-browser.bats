#!/usr/bin/env bats
bats_require_minimum_version 1.5.0

readonly CDP_BROWSER_MODULE="$BATS_TEST_DIRNAME/../../../../agents/skills/ponto/scripts/cdp-browser.js"
readonly CDP_TEST_PORT=19222
readonly TEST_PAGE_HTML='<html><head><title>CDP Test Page</title></head><body>
  <h1>Test Heading</h1>
  <p id="greeting">Hello World</p>
  <ul>
    <li class="fruit">Apple</li>
    <li class="fruit">Banana</li>
    <li class="fruit">Cherry</li>
  </ul>
  <button id="btn1">Click Me</button>
  <button id="btn2">Save</button>
  <button id="btn3">Cancel</button>
  <a href="#clicked" id="link1">More information</a>
  <div id="result"></div>
  <script>
    document.getElementById("btn1").addEventListener("click", () => {
      document.getElementById("result").textContent = "button-was-clicked";
    });
    document.getElementById("link1").addEventListener("click", (e) => {
      e.preventDefault();
      document.getElementById("result").textContent = "link-was-clicked";
    });
  </script>
</body></html>'

_find_chrome_binary() {
	command -v google-chrome-stable 2>/dev/null ||
		command -v chromium 2>/dev/null ||
		command -v chromium-browser 2>/dev/null ||
		echo ""
}

setup_file() {
	local chrome_binary
	chrome_binary=$(_find_chrome_binary)
	if [[ -z "$chrome_binary" ]]; then
		export CDP_TEST_SKIP_LIVE="no chrome/chromium binary found"
		return
	fi

	export CDP_TEST_USER_DATA_DIR
	CDP_TEST_USER_DATA_DIR=$(mktemp -d /tmp/cdp-test-profile-XXXXXX)

	"$chrome_binary" \
		--headless=new \
		--no-sandbox \
		--disable-gpu \
		--disable-extensions \
		--disable-background-networking \
		--disable-sync \
		--no-first-run \
		--no-default-browser-check \
		--user-data-dir="$CDP_TEST_USER_DATA_DIR" \
		--remote-debugging-port="$CDP_TEST_PORT" \
		about:blank &>/dev/null &
	export CDP_TEST_CHROME_PID=$!

	for _attempt in $(seq 1 30); do
		if curl -s "http://127.0.0.1:${CDP_TEST_PORT}/json/version" &>/dev/null; then
			return
		fi
		sleep 0.2
	done

	kill "$CDP_TEST_CHROME_PID" 2>/dev/null || true
	rm -rf "$CDP_TEST_USER_DATA_DIR"
	export CDP_TEST_SKIP_LIVE="headless chrome failed to start on port $CDP_TEST_PORT"
}

teardown_file() {
	if [[ -n "${CDP_TEST_CHROME_PID:-}" ]]; then
		kill "$CDP_TEST_CHROME_PID" 2>/dev/null || true
		wait "$CDP_TEST_CHROME_PID" 2>/dev/null || true
	fi
	if [[ -n "${CDP_TEST_USER_DATA_DIR:-}" ]]; then
		rm -rf "$CDP_TEST_USER_DATA_DIR"
	fi
}

_skip_unless_test_chrome_running() {
	if [[ -n "${CDP_TEST_SKIP_LIVE:-}" ]]; then
		skip "$CDP_TEST_SKIP_LIVE"
	fi
}

_navigate_to_test_page_and_get_frame() {
	cat <<JSEOF
import { connectToBrowser, CdpFrame } from '$CDP_BROWSER_MODULE';

const { browser, page } = await connectToBrowser();
const encodedHtml = encodeURIComponent(\`$TEST_PAGE_HTML\`);
await page.session.call('Page.navigate', { url: 'data:text/html,' + encodedHtml });
await page.waitForTimeout(1000);
await page.session.call('Runtime.disable');
page.executionContexts.clear();
await page.session.call('Runtime.enable');
await page.waitForTimeout(300);
const ctx = [...page.executionContexts.values()][0];
const frame = new CdpFrame(page.session, ctx.id);
JSEOF
}

@test "cdp-browser.js exists and is valid javascript" {
	[[ -f "$CDP_BROWSER_MODULE" ]]
	node --check "$CDP_BROWSER_MODULE"
}

@test "cdp-browser.js exports connectToBrowser, findPontoFrame, CdpFrame" {
	run node -e "
        import { connectToBrowser, findPontoFrame, CdpFrame } from '$CDP_BROWSER_MODULE';
        if (typeof connectToBrowser !== 'function') process.exit(1);
        if (typeof findPontoFrame !== 'function') process.exit(1);
        if (typeof CdpFrame !== 'function') process.exit(1);
        console.log('exports ok');
    "
	[[ "$status" -eq 0 ]]
	[[ "$output" == *"exports ok"* ]]
}

@test "connects to isolated headless chrome via CDP_PORT" {
	_skip_unless_test_chrome_running
	CDP_PORT="$CDP_TEST_PORT" run node -e "
        import { connectToBrowser } from '$CDP_BROWSER_MODULE';
        const { browser } = await connectToBrowser();
        console.log('connected');
        browser.close();
    "
	[[ "$status" -eq 0 ]]
	[[ "$output" == *"connected"* ]]
}

@test "connectToBrowser returns browser and page with correct API surface" {
	_skip_unless_test_chrome_running
	CDP_PORT="$CDP_TEST_PORT" run node -e "
        import { connectToBrowser } from '$CDP_BROWSER_MODULE';
        const { browser, page } = await connectToBrowser();
        const checks = [
            ['browser', !!browser],
            ['page', !!page],
            ['waitForTimeout', typeof page.waitForTimeout === 'function'],
            ['screenshot', typeof page.screenshot === 'function'],
            ['close', typeof browser.close === 'function'],
            ['executionContexts', page.executionContexts instanceof Map],
        ];
        for (const [name, ok] of checks) { if (!ok) { console.error('missing:', name); process.exit(1); } }
        console.log('api ok');
        browser.close();
    "
	[[ "$status" -eq 0 ]]
	[[ "$output" == *"api ok"* ]]
}

@test "page.screenshot produces valid PNG" {
	_skip_unless_test_chrome_running
	local screenshot="/tmp/cdp-test-screenshot-$$.png"
	CDP_PORT="$CDP_TEST_PORT" run node -e "
        import { connectToBrowser } from '$CDP_BROWSER_MODULE';
        const { browser, page } = await connectToBrowser();
        await page.screenshot({ path: '$screenshot' });
        browser.close();
        console.log('saved');
    "
	[[ "$status" -eq 0 ]]
	[[ -f "$screenshot" ]]
	file "$screenshot" | grep -q "PNG image data"
	rm -f "$screenshot"
}

@test "page.waitForTimeout delays at least the requested duration" {
	_skip_unless_test_chrome_running
	CDP_PORT="$CDP_TEST_PORT" run node -e "
        import { connectToBrowser } from '$CDP_BROWSER_MODULE';
        const { browser, page } = await connectToBrowser();
        const t = Date.now();
        await page.waitForTimeout(300);
        const elapsed = Date.now() - t;
        if (elapsed < 250) { console.error('too fast:', elapsed); process.exit(1); }
        console.log('waited', elapsed, 'ms');
        browser.close();
    "
	[[ "$status" -eq 0 ]]
	[[ "$output" == *"waited"* ]]
}

@test "frame.evaluate runs javascript and returns values" {
	_skip_unless_test_chrome_running
	CDP_PORT="$CDP_TEST_PORT" run node -e "$(_navigate_to_test_page_and_get_frame)
        const title = await frame.evaluate(() => document.title);
        if (title !== 'CDP Test Page') { console.error('bad title:', title); process.exit(1); }
        const obj = await frame.evaluate(() => ({ count: document.querySelectorAll('li').length }));
        if (obj.count !== 3) { console.error('bad count:', obj.count); process.exit(1); }
        console.log('evaluate ok');
        browser.close();
    "
	[[ "$status" -eq 0 ]]
	[[ "$output" == *"evaluate ok"* ]]
}

@test "frame.\$ finds single element and reads textContent" {
	_skip_unless_test_chrome_running
	CDP_PORT="$CDP_TEST_PORT" run node -e "$(_navigate_to_test_page_and_get_frame)
        const h1 = await frame.\$('h1');
        if (!h1) { console.error('h1 not found'); process.exit(1); }
        const text = await h1.textContent();
        if (text.trim() !== 'Test Heading') { console.error('bad text:', text); process.exit(1); }
        console.log('single query ok');
        browser.close();
    "
	[[ "$status" -eq 0 ]]
	[[ "$output" == *"single query ok"* ]]
}

@test "frame.\$ returns null for non-existent selector" {
	_skip_unless_test_chrome_running
	CDP_PORT="$CDP_TEST_PORT" run node -e "$(_navigate_to_test_page_and_get_frame)
        const nope = await frame.\$('#does-not-exist');
        if (nope !== null) { console.error('expected null'); process.exit(1); }
        console.log('null ok');
        browser.close();
    "
	[[ "$status" -eq 0 ]]
	[[ "$output" == *"null ok"* ]]
}

@test "frame.\$\$ returns array of CdpElements" {
	_skip_unless_test_chrome_running
	CDP_PORT="$CDP_TEST_PORT" run node -e "$(_navigate_to_test_page_and_get_frame)
        const fruits = await frame.\$\$('.fruit');
        if (!Array.isArray(fruits) || fruits.length !== 3) {
            console.error('bad fruits:', fruits?.length); process.exit(1);
        }
        const texts = [];
        for (const f of fruits) texts.push((await f.textContent()).trim());
        if (texts.join(',') !== 'Apple,Banana,Cherry') {
            console.error('bad texts:', texts); process.exit(1);
        }
        console.log('array query ok');
        browser.close();
    "
	[[ "$status" -eq 0 ]]
	[[ "$output" == *"array query ok"* ]]
}

@test "element.\$ does scoped child query" {
	_skip_unless_test_chrome_running
	CDP_PORT="$CDP_TEST_PORT" run node -e "$(_navigate_to_test_page_and_get_frame)
        const ul = await frame.\$('ul');
        const first = await ul.\$('li:first-child');
        const text = await first.textContent();
        if (text.trim() !== 'Apple') { console.error('bad child:', text); process.exit(1); }
        console.log('scoped ok');
        browser.close();
    "
	[[ "$status" -eq 0 ]]
	[[ "$output" == *"scoped ok"* ]]
}

@test ":has-text pseudo-selector finds element by text" {
	_skip_unless_test_chrome_running
	CDP_PORT="$CDP_TEST_PORT" run node -e "$(_navigate_to_test_page_and_get_frame)
        const btn = await frame.\$('button:has-text(\"Save\")');
        if (!btn) { console.error('Save not found'); process.exit(1); }
        const text = await btn.textContent();
        if (text.trim() !== 'Save') { console.error('bad text:', text); process.exit(1); }
        console.log('has-text ok');
        browser.close();
    "
	[[ "$status" -eq 0 ]]
	[[ "$output" == *"has-text ok"* ]]
}

@test ":has-text returns null when text does not match" {
	_skip_unless_test_chrome_running
	CDP_PORT="$CDP_TEST_PORT" run node -e "$(_navigate_to_test_page_and_get_frame)
        const nope = await frame.\$('button:has-text(\"Nonexistent\")');
        if (nope !== null) { console.error('expected null'); process.exit(1); }
        console.log('no match ok');
        browser.close();
    "
	[[ "$status" -eq 0 ]]
	[[ "$output" == *"no match ok"* ]]
}

@test "comma-separated :has-text selectors find first match" {
	_skip_unless_test_chrome_running
	CDP_PORT="$CDP_TEST_PORT" run node -e "$(_navigate_to_test_page_and_get_frame)
        const el = await frame.\$('button:has-text(\"Cancel\"), button:has-text(\"Save\")');
        if (!el) { console.error('no match'); process.exit(1); }
        const text = await el.textContent();
        if (text.trim() !== 'Cancel' && text.trim() !== 'Save') {
            console.error('unexpected:', text); process.exit(1);
        }
        console.log('comma ok:', text.trim());
        browser.close();
    "
	[[ "$status" -eq 0 ]]
	[[ "$output" == *"comma ok"* ]]
}

@test "element.click triggers DOM event handler" {
	_skip_unless_test_chrome_running
	CDP_PORT="$CDP_TEST_PORT" run node -e "$(_navigate_to_test_page_and_get_frame)
        const btn = await frame.\$('#btn1');
        await btn.click();
        await page.waitForTimeout(300);
        const result = await frame.evaluate(() => document.getElementById('result').textContent);
        if (result !== 'button-was-clicked') { console.error('click failed:', result); process.exit(1); }
        console.log('click ok');
        browser.close();
    "
	[[ "$status" -eq 0 ]]
	[[ "$output" == *"click ok"* ]]
}

@test "click on :has-text selected link triggers handler" {
	_skip_unless_test_chrome_running
	CDP_PORT="$CDP_TEST_PORT" run node -e "$(_navigate_to_test_page_and_get_frame)
        const link = await frame.\$('a:has-text(\"More information\")');
        if (!link) { console.error('link not found'); process.exit(1); }
        await link.click();
        await page.waitForTimeout(300);
        const result = await frame.evaluate(() => document.getElementById('result').textContent);
        if (result !== 'link-was-clicked') { console.error('link click failed:', result); process.exit(1); }
        console.log('link click ok');
        browser.close();
    "
	[[ "$status" -eq 0 ]]
	[[ "$output" == *"link click ok"* ]]
}

@test "element.\$\$ with :has-text on child scope" {
	_skip_unless_test_chrome_running
	CDP_PORT="$CDP_TEST_PORT" run node -e "$(_navigate_to_test_page_and_get_frame)
        const body = await frame.\$('body');
        const btns = await body.\$\$('button');
        if (btns.length !== 3) { console.error('expected 3 buttons:', btns.length); process.exit(1); }
        const saveBtn = await body.\$('button:has-text(\"Save\")');
        if (!saveBtn) { console.error('scoped has-text failed'); process.exit(1); }
        console.log('child has-text ok');
        browser.close();
    "
	[[ "$status" -eq 0 ]]
	[[ "$output" == *"child has-text ok"* ]]
}

@test "screenshot after interaction captures current state" {
	_skip_unless_test_chrome_running
	local screenshot="/tmp/cdp-interaction-screenshot-$$.png"
	CDP_PORT="$CDP_TEST_PORT" run node -e "$(_navigate_to_test_page_and_get_frame)
        const btn = await frame.\$('#btn1');
        await btn.click();
        await page.waitForTimeout(300);
        await page.screenshot({ path: '$screenshot' });
        console.log('interaction screenshot saved');
        browser.close();
    "
	[[ "$status" -eq 0 ]]
	[[ -f "$screenshot" ]]
	file "$screenshot" | grep -q "PNG image data"
	rm -f "$screenshot"
}

@test "pw CLI is no longer in PATH" {
	run which pw
	[[ "$status" -ne 0 ]]
}

@test "agent-browser package files are removed" {
	[[ ! -f "$BATS_TEST_DIRNAME/../agent-browser-package.nix" ]]
	[[ ! -f "$BATS_TEST_DIRNAME/../scripts.nix" ]]
}

@test "deleted pw and playwright files do not exist" {
	[[ ! -f "$BATS_TEST_DIRNAME/../../agents/skills/browser/scripts/pw.sh" ]]
	[[ ! -f "$BATS_TEST_DIRNAME/../../agents/skills/browser/scripts/pw.js" ]]
	[[ ! -f "$BATS_TEST_DIRNAME/../../agents/skills/browser/scripts/pw-daemon.js" ]]
	[[ ! -f "$BATS_TEST_DIRNAME/../../agents/skills/browser/default.nix" ]]
	[[ ! -f "$BATS_TEST_DIRNAME/../../agents/skills/ponto/scripts/playwright-resolver.js" ]]
	[[ ! -f "$BATS_TEST_DIRNAME/../../home/modules/playwright.nix" ]]
}

@test "no stale PW_PORT or playwright-resolver references" {
	local codebase="$BATS_TEST_DIRNAME/../.."
	run ! grep -r --include='*.js' --include='*.sh' --include='*.nix' \
		'PW_PORT' "$codebase/agents" "$codebase/home" 2>/dev/null
	run ! grep -r --include='*.js' --include='*.sh' --include='*.nix' \
		'playwright-resolver' "$codebase/agents" "$codebase/home" 2>/dev/null
}
