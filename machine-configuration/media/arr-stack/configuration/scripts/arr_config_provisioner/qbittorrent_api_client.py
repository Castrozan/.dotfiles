import http.cookiejar
import json
import urllib.parse
import urllib.request

FORM_ENCODED_HEADERS = {"Content-Type": "application/x-www-form-urlencoded"}


def build_authenticated_opener(base_url, username, password):
    opener = urllib.request.build_opener(
        urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar())
    )
    login_request = urllib.request.Request(
        f"{base_url}/api/v2/auth/login",
        data=urllib.parse.urlencode(
            {"username": username, "password": password}
        ).encode(),
        headers={**FORM_ENCODED_HEADERS, "Referer": base_url},
    )
    with opener.open(login_request, timeout=30) as response:
        if response.read().decode().strip() != "Ok.":
            raise RuntimeError("qbittorrent rejected the web ui login")
    return opener


def read_preferences(opener, base_url):
    with opener.open(f"{base_url}/api/v2/app/preferences", timeout=30) as response:
        return json.loads(response.read().decode())


def write_preferences(opener, base_url, preferences):
    write_request = urllib.request.Request(
        f"{base_url}/api/v2/app/setPreferences",
        data=urllib.parse.urlencode({"json": json.dumps(preferences)}).encode(),
        headers={**FORM_ENCODED_HEADERS, "Referer": base_url},
    )
    with opener.open(write_request, timeout=30) as response:
        response.read()
