#!/usr/bin/env python3
import json
import os
import sqlite3
import sys
import shutil
import tempfile
from pathlib import Path

from Crypto.Cipher import AES
from Crypto.Protocol.KDF import PBKDF2

BROWSER_DIRECTORIES = [
    Path.home() / ".config/google-chrome",
    Path.home() / ".config/chromium",
    Path.home() / ".config/BraveSoftware/Brave-Browser",
]

TWIKIT_COOKIES_PATH = Path(
    os.environ.get(
        "TWIKIT_COOKIES_PATH", str(Path.home() / ".config" / "twikit" / "cookies.json")
    )
)

REQUIRED_COOKIE_NAMES = ["auth_token", "ct0"]
X_DOMAINS = [".x.com", ".twitter.com", "x.com", "twitter.com"]
CBC_GARBAGE_PREFIX = "d}\u07a4"


def find_all_browser_cookies_databases():
    databases = []
    for browser_directory in BROWSER_DIRECTORIES:
        if not browser_directory.exists():
            continue
        for profile_directory in sorted(browser_directory.iterdir()):
            cookies_file = profile_directory / "Cookies"
            if cookies_file.exists():
                databases.append(cookies_file)
    return databases


def get_chrome_encryption_key():
    try:
        import secretstorage

        connection = secretstorage.dbus_init()
        collection = secretstorage.get_default_collection(connection)
        for item in collection.get_all_items():
            if "Chrome" in item.get_label() or "Chromium" in item.get_label():
                password = item.get_secret().decode("utf-8")
                return PBKDF2(password, b"saltysalt", dkLen=16, count=1)
    except Exception:
        pass
    return PBKDF2("peanuts", b"saltysalt", dkLen=16, count=1)


def decrypt_chrome_cookie_value(encrypted_value, encryption_key):
    if not encrypted_value or len(encrypted_value) <= 3:
        return None
    prefix = encrypted_value[:3]
    if prefix not in (b"v10", b"v11"):
        return None
    initialization_vector = b" " * 16
    cipher = AES.new(encryption_key, AES.MODE_CBC, initialization_vector)
    decrypted = cipher.decrypt(encrypted_value[3:])
    padding_length = decrypted[-1]
    if 0 < padding_length <= 16:
        decrypted = decrypted[:-padding_length]
    try:
        value = decrypted.decode("utf-8")
    except UnicodeDecodeError:
        for start_offset in range(len(decrypted)):
            try:
                candidate = decrypted[start_offset:].decode("utf-8")
                if candidate:
                    value = candidate
                    break
            except UnicodeDecodeError:
                continue
        else:
            return None
    if value.startswith(CBC_GARBAGE_PREFIX):
        value = value[len(CBC_GARBAGE_PREFIX) :]
    if len(value) > 2 and value.startswith('"') and value.endswith('"'):
        value = value[1:-1]
    return value if value else None


def extract_x_cookies_from_database(database_path, encryption_key):
    temporary_copy = tempfile.mktemp(suffix=".db")
    shutil.copy2(str(database_path), temporary_copy)
    try:
        connection = sqlite3.connect(temporary_copy)
        cursor = connection.cursor()
        domain_conditions = " OR ".join(
            [f"host_key = '{domain}'" for domain in X_DOMAINS]
            + [f"host_key LIKE '%.{domain}'" for domain in X_DOMAINS]
        )
        cursor.execute(
            f"SELECT name, value, encrypted_value FROM cookies WHERE {domain_conditions}"
        )
        cookies = {}
        for name, plain_value, encrypted_value in cursor.fetchall():
            if plain_value:
                cookies[name] = plain_value
            else:
                decrypted = decrypt_chrome_cookie_value(encrypted_value, encryption_key)
                if decrypted:
                    cookies[name] = decrypted
        connection.close()
        return cookies
    finally:
        os.unlink(temporary_copy)


def main():
    databases = find_all_browser_cookies_databases()
    if not databases:
        print(
            json.dumps(
                {
                    "error": "No browser cookies database found",
                    "searched": [str(d) for d in BROWSER_DIRECTORIES],
                }
            )
        )
        sys.exit(1)

    encryption_key = get_chrome_encryption_key()

    for database_path in databases:
        print(f"Checking: {database_path}", file=sys.stderr)
        cookies = extract_x_cookies_from_database(database_path, encryption_key)
        missing = [name for name in REQUIRED_COOKIE_NAMES if name not in cookies]
        if not missing:
            TWIKIT_COOKIES_PATH.parent.mkdir(parents=True, exist_ok=True)
            TWIKIT_COOKIES_PATH.write_text(json.dumps(cookies, indent=2))
            os.chmod(str(TWIKIT_COOKIES_PATH), 0o600)
            print(
                f"Exported {len(cookies)} cookies from {database_path} to {TWIKIT_COOKIES_PATH}",
                file=sys.stderr,
            )
            print(
                json.dumps(
                    {
                        "status": "ok",
                        "cookies_count": len(cookies),
                        "source": str(database_path),
                        "path": str(TWIKIT_COOKIES_PATH),
                    }
                )
            )
            return

    print(
        json.dumps(
            {
                "error": "No browser profile has both auth_token and ct0 cookies. Log into x.com in Chrome first.",
                "searched": [str(db) for db in databases],
            }
        )
    )
    sys.exit(1)


if __name__ == "__main__":
    main()
