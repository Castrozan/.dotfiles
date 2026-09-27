#!/usr/bin/env python3
"""Extract X/Twitter cookies from a browser cookies file and save in twikit format.

Reads cookies from a Chromium-based browser's cookie database
and exports them as JSON for twikit's load_cookies().
"""

import json
import os
import sqlite3
import sys
import shutil
import tempfile
from contextlib import closing
from pathlib import Path

BROWSER_COOKIE_PATHS = [
    Path.home() / ".pinchtab/chrome-profile/Default/Cookies",
    Path.home() / ".config/BraveSoftware/Brave-Browser/Default/Cookies",
    Path.home() / ".config/google-chrome/Default/Cookies",
    Path.home() / ".config/chromium/Default/Cookies",
]

TWIKIT_COOKIES_PATH = Path(
    os.environ.get(
        "TWIKIT_COOKIES_PATH", str(Path.home() / ".config" / "twikit" / "cookies.json")
    )
)

REQUIRED_COOKIE_NAMES = ["auth_token", "ct0"]
X_DOMAINS = [".x.com", ".twitter.com", "x.com", "twitter.com"]


def find_browser_cookies_database():
    """Find the first available browser cookies database."""
    for cookie_path in BROWSER_COOKIE_PATHS:
        if cookie_path.exists():
            return cookie_path
    return None


def extract_x_cookies_from_database(database_path):
    """Extract X/Twitter cookies from a Chromium cookies database."""
    with tempfile.NamedTemporaryFile(suffix=".db") as temporary_copy:
        with Path(database_path).open("rb") as database:
            shutil.copyfileobj(database, temporary_copy)
        temporary_copy.flush()
        domain_conditions = " OR ".join(
            [f"host_key = '{domain}'" for domain in X_DOMAINS]
            + [f"host_key LIKE '%.{domain}'" for domain in X_DOMAINS]
        )

        with closing(sqlite3.connect(temporary_copy.name)) as connection:
            cursor = connection.execute(
                f"SELECT name, value, host_key FROM cookies WHERE {domain_conditions}"
            )
            return {name: value for name, value, host_key in cursor if value}


def main():
    database_path = find_browser_cookies_database()

    if not database_path:
        print(
            json.dumps(
                {
                    "error": "No browser cookies database found",
                    "searched": [str(p) for p in BROWSER_COOKIE_PATHS],
                }
            )
        )
        sys.exit(1)

    print(f"Reading cookies from: {database_path}", file=sys.stderr)

    cookies = extract_x_cookies_from_database(database_path)

    missing_cookies = [name for name in REQUIRED_COOKIE_NAMES if name not in cookies]
    if missing_cookies:
        print(
            json.dumps(
                {
                    "error": f"Missing required cookies: {missing_cookies}. Are you logged into X in the browser?",
                    "found_cookies": list(cookies.keys()),
                }
            )
        )
        sys.exit(1)

    TWIKIT_COOKIES_PATH.parent.mkdir(parents=True, exist_ok=True)
    TWIKIT_COOKIES_PATH.write_text(json.dumps(cookies, indent=2))
    os.chmod(str(TWIKIT_COOKIES_PATH), 0o600)

    print(f"Exported {len(cookies)} cookies to {TWIKIT_COOKIES_PATH}", file=sys.stderr)
    print(
        json.dumps(
            {
                "status": "ok",
                "cookies_count": len(cookies),
                "path": str(TWIKIT_COOKIES_PATH),
            }
        )
    )


if __name__ == "__main__":
    main()
