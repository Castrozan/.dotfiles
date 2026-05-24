"""Cookie loading, credential-based login, and authenticated client construction."""

import json
import os
import sys

from twikit_cli_serializers import (
    COOKIES_PATH,
    EMAIL_FILE,
    PASSWORD_FILE,
    USERNAME_FILE,
    read_secret_file,
)


async def get_client():
    from twikit import Client

    client = Client("en-US")

    if COOKIES_PATH.exists():
        client.load_cookies(str(COOKIES_PATH))
        return client

    username = read_secret_file(USERNAME_FILE)
    email = read_secret_file(EMAIL_FILE)
    password = read_secret_file(PASSWORD_FILE)

    if not all([username, email, password]):
        print(
            json.dumps(
                {"error": "No cookies and no credentials found. Run: twikit-cli login"}
            ),
            file=sys.stderr,
        )
        sys.exit(1)

    print(
        f"[twikit-cli] No cookies found. Logging in as {username}...", file=sys.stderr
    )

    COOKIES_PATH.parent.mkdir(parents=True, exist_ok=True)

    await client.login(
        auth_info_1=username,
        auth_info_2=email,
        password=password,
    )

    client.save_cookies(str(COOKIES_PATH))
    os.chmod(str(COOKIES_PATH), 0o600)
    print(f"[twikit-cli] Cookies saved to {COOKIES_PATH}", file=sys.stderr)

    return client


async def command_login(args):
    from twikit import Client

    client = Client("en-US")

    COOKIES_PATH.parent.mkdir(parents=True, exist_ok=True)

    if COOKIES_PATH.exists():
        print(f"Loading existing cookies from {COOKIES_PATH}")
        client.load_cookies(str(COOKIES_PATH))
        try:
            user_id = await client.user_id()
            print(f"Already authenticated as user {user_id}")
            return
        except Exception:
            print("Existing cookies expired, need fresh login")

    username = read_secret_file(USERNAME_FILE)
    email = read_secret_file(EMAIL_FILE)
    password = read_secret_file(PASSWORD_FILE)

    if not all([username, email, password]):
        print("No agenix secrets found, falling back to interactive login")
        username = input("X username: ")
        email = input("X email: ")
        password = input("X password: ")

    totp_secret = None
    if args.totp:
        totp_secret = args.totp

    print(f"Logging in as {username}...")

    await client.login(
        auth_info_1=username,
        auth_info_2=email,
        password=password,
        totp_secret=totp_secret,
    )

    client.save_cookies(str(COOKIES_PATH))
    os.chmod(str(COOKIES_PATH), 0o600)
    print(f"Cookies saved to {COOKIES_PATH}")
