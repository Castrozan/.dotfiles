from __future__ import annotations

import argparse
import contextlib
import json
import os
import re
import shutil
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

from playwright.sync_api import (
    BrowserContext,
    Locator,
    Page,
    Playwright,
    sync_playwright,
)

default_google_chat_home_url = "https://chat.google.com/"
default_browser_profile_directory = (
    Path.home() / ".local" / "share" / "google-chat-browser-cli" / "chrome-profile"
)
default_login_wait_seconds = 600
default_browser_wait_seconds = 30
default_viewport_width = 1440
default_viewport_height = 960
google_sign_in_url_pattern = re.compile(
    r"accounts\.google\.com|ServiceLogin", re.IGNORECASE
)
google_chat_url_pattern = re.compile(r"^https://chat\.google\.com/", re.IGNORECASE)
message_composer_label_pattern = re.compile(
    r"send a message|enviar uma mensagem|message to|mensagem para",
    re.IGNORECASE,
)
send_button_label_pattern = re.compile(r"send|enviar", re.IGNORECASE)


def print_log_message(message: str) -> None:
    print(message, file=sys.stderr)


def resolve_profile_directory(profile_directory_argument: str | None) -> Path:
    if profile_directory_argument:
        return Path(profile_directory_argument).expanduser()
    return default_browser_profile_directory


def resolve_message_text(
    message_argument: str | None, message_file_argument: str | None
) -> str:
    if bool(message_argument) == bool(message_file_argument):
        raise RuntimeError("Provide exactly one of --message or --message-file")

    if message_argument is not None:
        resolved_message = message_argument
    elif message_file_argument == "-":
        resolved_message = sys.stdin.read()
    else:
        resolved_message = (
            Path(message_file_argument or "").expanduser().read_text(encoding="utf-8")
        )

    normalized_message = resolved_message.rstrip("\n")
    if not normalized_message.strip():
        raise RuntimeError("Message cannot be empty")

    return normalized_message


def create_message_preview(message_text: str, preview_length: int = 80) -> str:
    single_line_message = " ".join(message_text.split())
    if len(single_line_message) <= preview_length:
        return single_line_message
    return f"{single_line_message[:preview_length].rstrip()}..."


def resolve_browser_executable(browser_executable_argument: str | None) -> str:
    browser_candidates: list[str] = []

    if browser_executable_argument:
        browser_candidates.append(browser_executable_argument)

    environment_browser_executable = os.environ.get(
        "GOOGLE_CHAT_BROWSER_DEFAULT_EXECUTABLE"
    )
    if environment_browser_executable:
        browser_candidates.append(environment_browser_executable)

    browser_candidates.extend(
        [
            "google-chrome-stable",
            "google-chrome",
            "chromium",
            "chromium-browser",
        ]
    )

    for browser_candidate in browser_candidates:
        expanded_candidate_path = Path(browser_candidate).expanduser()
        if expanded_candidate_path.is_file():
            return str(expanded_candidate_path)

        discovered_candidate_path = shutil.which(browser_candidate)
        if discovered_candidate_path:
            return discovered_candidate_path

    raise RuntimeError(
        "No Chromium-based browser executable found. Use --browser-executable "
        "or set GOOGLE_CHAT_BROWSER_DEFAULT_EXECUTABLE"
    )


def ensure_parent_directory_exists(file_path: str | None) -> None:
    if not file_path:
        return
    Path(file_path).expanduser().parent.mkdir(parents=True, exist_ok=True)


def start_browser_context(
    profile_directory: Path,
    browser_executable: str,
    headless: bool,
) -> tuple[Playwright, BrowserContext]:
    profile_directory.mkdir(parents=True, exist_ok=True)

    playwright = sync_playwright().start()
    try:
        browser_context = playwright.chromium.launch_persistent_context(
            str(profile_directory),
            headless=headless,
            executable_path=browser_executable,
            viewport={
                "width": default_viewport_width,
                "height": default_viewport_height,
            },
            args=[
                "--disable-dev-shm-usage",
                "--disable-setuid-sandbox",
                "--no-default-browser-check",
                "--no-first-run",
                "--no-sandbox",
            ],
        )
    except Exception:
        playwright.stop()
        raise

    return playwright, browser_context


def close_browser_context(
    playwright: Playwright, browser_context: BrowserContext
) -> None:
    browser_context.close()
    playwright.stop()


def create_clean_working_page(browser_context: BrowserContext) -> Page:
    for existing_page in list(browser_context.pages):
        with contextlib.suppress(Exception):
            existing_page.close()

    working_page = browser_context.new_page()
    working_page.bring_to_front()
    return working_page


def navigate_to_google_chat_destination(
    page: Page, destination_url: str, wait_seconds: int
) -> None:
    print_log_message(f"Opening {destination_url}")
    page.goto(
        destination_url, wait_until="domcontentloaded", timeout=wait_seconds * 1000
    )
    page.wait_for_timeout(2000)


def ensure_google_sign_in_is_not_required(page: Page) -> None:
    if google_sign_in_url_pattern.search(page.url):
        raise RuntimeError(
            "Google sign-in is required for this profile. Run `google-chat-browser-cli "
            "login --headed` first."
        )


def wait_for_google_chat_session(
    page: Page,
    wait_seconds: int,
    allow_google_sign_in_flow: bool = False,
) -> None:
    deadline = time.time() + wait_seconds

    while time.time() < deadline:
        if not allow_google_sign_in_flow:
            ensure_google_sign_in_is_not_required(page)
        if google_chat_url_pattern.search(
            page.url
        ) and not google_sign_in_url_pattern.search(page.url):
            return
        page.wait_for_timeout(1000)

    raise RuntimeError("Google Chat session did not become ready before the timeout")


def select_first_visible_locator(candidate_locators: Locator) -> Locator | None:
    for locator_index in range(candidate_locators.count()):
        candidate_locator = candidate_locators.nth(locator_index)
        if candidate_locator.is_visible():
            return candidate_locator
    return None


def find_message_composer(page: Page) -> Locator | None:
    labeled_message_composer = select_first_visible_locator(
        page.get_by_role("textbox", name=message_composer_label_pattern)
    )
    if labeled_message_composer:
        return labeled_message_composer

    contenteditable_textboxes = page.locator(
        'div[contenteditable="true"][role="textbox"][aria-label]'
    )
    for locator_index in range(contenteditable_textboxes.count()):
        candidate_locator = contenteditable_textboxes.nth(locator_index)
        if not candidate_locator.is_visible():
            continue

        accessible_label = candidate_locator.get_attribute("aria-label") or ""
        if message_composer_label_pattern.search(accessible_label):
            return candidate_locator

    return None


def wait_for_message_composer(page: Page, wait_seconds: int) -> Locator:
    deadline = time.time() + wait_seconds

    while time.time() < deadline:
        ensure_google_sign_in_is_not_required(page)
        discovered_message_composer = find_message_composer(page)
        if discovered_message_composer:
            return discovered_message_composer
        page.wait_for_timeout(1000)

    raise RuntimeError(
        "Message composer not found. Check the target space URL and stored login"
    )


def clear_and_fill_message_composer(
    page: Page, message_composer: Locator, message_text: str
) -> None:
    message_lines = message_text.splitlines() or [""]
    message_composer.click()
    page.keyboard.press("ControlOrMeta+A")
    page.keyboard.press("Backspace")

    for message_line_index, message_line in enumerate(message_lines):
        if message_line:
            page.keyboard.insert_text(message_line)
        if message_line_index < len(message_lines) - 1:
            page.keyboard.press("Shift+Enter")


def find_send_button(page: Page) -> Locator | None:
    labeled_send_button = select_first_visible_locator(
        page.get_by_role("button", name=send_button_label_pattern)
    )
    if labeled_send_button:
        return labeled_send_button

    send_button_candidates = page.locator("button[aria-label]")
    for locator_index in range(send_button_candidates.count()):
        candidate_locator = send_button_candidates.nth(locator_index)
        if not candidate_locator.is_visible():
            continue

        accessible_label = candidate_locator.get_attribute("aria-label") or ""
        if send_button_label_pattern.search(accessible_label):
            return candidate_locator

    return None


def wait_for_send_button(page: Page, wait_seconds: int) -> Locator:
    deadline = time.time() + wait_seconds

    while time.time() < deadline:
        discovered_send_button = find_send_button(page)
        if discovered_send_button and discovered_send_button.is_enabled():
            return discovered_send_button
        page.wait_for_timeout(500)

    raise RuntimeError("Send button not found or not enabled")


def wait_for_message_dispatch(
    page: Page, message_composer: Locator, wait_seconds: int
) -> None:
    message_composer_handle = message_composer.element_handle()
    if message_composer_handle is None:
        return

    page.wait_for_function(
        "(element) => !element || !element.isConnected || "
        "((element.innerText || '').trim() === '')",
        arg=message_composer_handle,
        timeout=wait_seconds * 1000,
    )


def maybe_take_screenshot(page: Page, screenshot_path_argument: str | None) -> None:
    if not screenshot_path_argument:
        return

    ensure_parent_directory_exists(screenshot_path_argument)
    page.screenshot(
        path=str(Path(screenshot_path_argument).expanduser()), full_page=True
    )
    print_log_message(f"Saved screenshot to {screenshot_path_argument}")


def login_to_google_chat(
    browser_executable: str,
    profile_directory: Path,
    destination_url: str,
    wait_seconds: int,
    screenshot_path_argument: str | None,
) -> dict[str, object]:
    playwright, browser_context = start_browser_context(
        profile_directory=profile_directory,
        browser_executable=browser_executable,
        headless=False,
    )

    try:
        working_page = create_clean_working_page(browser_context)
        navigate_to_google_chat_destination(working_page, destination_url, wait_seconds)
        print_log_message(
            "Complete the Google sign-in flow in the opened browser window"
        )
        wait_for_google_chat_session(
            working_page,
            wait_seconds,
            allow_google_sign_in_flow=True,
        )
        maybe_take_screenshot(working_page, screenshot_path_argument)
        return {
            "success": True,
            "mode": "login",
            "url": working_page.url,
            "title": working_page.title(),
            "browser_executable": browser_executable,
            "profile_directory": str(profile_directory),
        }
    finally:
        close_browser_context(playwright, browser_context)


def get_google_chat_session_status(
    browser_executable: str,
    profile_directory: Path,
    wait_seconds: int,
    screenshot_path_argument: str | None,
) -> dict[str, object]:
    playwright, browser_context = start_browser_context(
        profile_directory=profile_directory,
        browser_executable=browser_executable,
        headless=True,
    )

    try:
        working_page = create_clean_working_page(browser_context)
        navigate_to_google_chat_destination(
            working_page, default_google_chat_home_url, wait_seconds
        )
        wait_for_google_chat_session(working_page, wait_seconds)
        maybe_take_screenshot(working_page, screenshot_path_argument)
        return {
            "success": True,
            "mode": "session-status",
            "url": working_page.url,
            "title": working_page.title(),
            "browser_executable": browser_executable,
            "profile_directory": str(profile_directory),
        }
    finally:
        close_browser_context(playwright, browser_context)


def send_google_chat_message(
    browser_executable: str,
    profile_directory: Path,
    space_url: str,
    message_text: str,
    headless: bool,
    wait_seconds: int,
    screenshot_path_argument: str | None,
) -> dict[str, object]:
    playwright, browser_context = start_browser_context(
        profile_directory=profile_directory,
        browser_executable=browser_executable,
        headless=headless,
    )

    try:
        working_page = create_clean_working_page(browser_context)
        navigate_to_google_chat_destination(working_page, space_url, wait_seconds)
        message_composer = wait_for_message_composer(working_page, wait_seconds)
        clear_and_fill_message_composer(working_page, message_composer, message_text)
        working_page.wait_for_timeout(300)
        send_button = wait_for_send_button(working_page, wait_seconds)
        print_log_message(f"Sending message to {working_page.url}")
        send_button.click()
        wait_for_message_dispatch(working_page, message_composer, wait_seconds)
        maybe_take_screenshot(working_page, screenshot_path_argument)
        return {
            "success": True,
            "mode": "browser",
            "space_url": working_page.url,
            "title": working_page.title(),
            "browser_executable": browser_executable,
            "profile_directory": str(profile_directory),
            "message_length": len(message_text),
            "message_preview": create_message_preview(message_text),
        }
    finally:
        close_browser_context(playwright, browser_context)


def send_google_chat_webhook_message(
    webhook_url: str,
    message_text: str,
) -> dict[str, object]:
    request_payload = json.dumps({"text": message_text}).encode("utf-8")
    webhook_request = urllib.request.Request(
        webhook_url,
        data=request_payload,
        headers={"Content-Type": "application/json; charset=UTF-8"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(webhook_request, timeout=30) as webhook_response:
            response_body = webhook_response.read().decode("utf-8").strip()
            parsed_response_body: object
            if response_body:
                try:
                    parsed_response_body = json.loads(response_body)
                except json.JSONDecodeError:
                    parsed_response_body = response_body
            else:
                parsed_response_body = ""

            return {
                "success": True,
                "mode": "webhook",
                "status_code": webhook_response.status,
                "message_length": len(message_text),
                "message_preview": create_message_preview(message_text),
                "response": parsed_response_body,
            }
    except urllib.error.HTTPError as error:
        error_body = error.read().decode("utf-8").strip()
        raise RuntimeError(
            f"Webhook request failed with HTTP {error.code}: {error_body}"
        ) from None
    except urllib.error.URLError as error:
        raise RuntimeError(f"Webhook request failed: {error.reason}") from None


def build_argument_parser() -> argparse.ArgumentParser:
    argument_parser = argparse.ArgumentParser(
        prog="google-chat-browser-cli",
        description=(
            "Send Google Chat messages through a persistent browser session or webhook."
        ),
    )
    subcommands = argument_parser.add_subparsers(dest="command", required=True)

    login_subcommand = subcommands.add_parser(
        "login",
        help=(
            "Open a headed browser session and wait for Google Chat login to complete."
        ),
    )
    login_subcommand.add_argument(
        "--space-url",
        default=default_google_chat_home_url,
        help="Google Chat URL to open while preparing the persistent session.",
    )
    login_subcommand.add_argument(
        "--headed",
        action="store_true",
        help="Accepted for compatibility. Login always runs with a visible browser.",
    )
    login_subcommand.add_argument(
        "--profile-dir",
        help="Persistent browser profile directory.",
    )
    login_subcommand.add_argument(
        "--browser-executable",
        help="Path or executable name for Chrome/Chromium.",
    )
    login_subcommand.add_argument(
        "--wait-seconds",
        type=int,
        default=default_login_wait_seconds,
        help="Seconds to wait for the login flow to finish.",
    )
    login_subcommand.add_argument(
        "--screenshot",
        help="Save a screenshot after the session becomes ready.",
    )

    session_status_subcommand = subcommands.add_parser(
        "session-status",
        help="Check whether the stored Google Chat browser session is ready.",
    )
    session_status_subcommand.add_argument(
        "--profile-dir",
        help="Persistent browser profile directory.",
    )
    session_status_subcommand.add_argument(
        "--browser-executable",
        help="Path or executable name for Chrome/Chromium.",
    )
    session_status_subcommand.add_argument(
        "--wait-seconds",
        type=int,
        default=default_browser_wait_seconds,
        help="Seconds to wait for Google Chat to load.",
    )
    session_status_subcommand.add_argument(
        "--screenshot",
        help="Save a screenshot after the session becomes ready.",
    )

    send_message_subcommand = subcommands.add_parser(
        "send-message",
        help="Send a message to a Google Chat space or DM through browser automation.",
    )
    send_message_subcommand.add_argument(
        "--space-url",
        required=True,
        help="Full Google Chat URL for the target space or DM.",
    )
    send_message_subcommand.add_argument(
        "--message",
        help="Inline message text.",
    )
    send_message_subcommand.add_argument(
        "--message-file",
        help="Read the message from a file path or use - for stdin.",
    )
    send_message_subcommand.add_argument(
        "--profile-dir",
        help="Persistent browser profile directory.",
    )
    send_message_subcommand.add_argument(
        "--browser-executable",
        help="Path or executable name for Chrome/Chromium.",
    )
    send_message_subcommand.add_argument(
        "--wait-seconds",
        type=int,
        default=default_browser_wait_seconds,
        help="Seconds to wait for Google Chat and the composer.",
    )
    send_message_subcommand.add_argument(
        "--headed",
        action="store_true",
        help="Run the browser visibly instead of headless.",
    )
    send_message_subcommand.add_argument(
        "--screenshot",
        help="Save a screenshot after sending the message.",
    )

    send_webhook_subcommand = subcommands.add_parser(
        "send-webhook",
        help="Send a message to an existing Google Chat incoming webhook.",
    )
    send_webhook_subcommand.add_argument(
        "--webhook-url",
        required=True,
        help="Incoming webhook URL for the target Google Chat space.",
    )
    send_webhook_subcommand.add_argument(
        "--message",
        help="Inline message text.",
    )
    send_webhook_subcommand.add_argument(
        "--message-file",
        help="Read the message from a file path or use - for stdin.",
    )

    return argument_parser


def run_command(parsed_arguments: argparse.Namespace) -> dict[str, object]:
    if parsed_arguments.command == "login":
        return login_to_google_chat(
            browser_executable=resolve_browser_executable(
                parsed_arguments.browser_executable
            ),
            profile_directory=resolve_profile_directory(parsed_arguments.profile_dir),
            destination_url=parsed_arguments.space_url,
            wait_seconds=parsed_arguments.wait_seconds,
            screenshot_path_argument=parsed_arguments.screenshot,
        )

    if parsed_arguments.command == "session-status":
        return get_google_chat_session_status(
            browser_executable=resolve_browser_executable(
                parsed_arguments.browser_executable
            ),
            profile_directory=resolve_profile_directory(parsed_arguments.profile_dir),
            wait_seconds=parsed_arguments.wait_seconds,
            screenshot_path_argument=parsed_arguments.screenshot,
        )

    if parsed_arguments.command == "send-message":
        return send_google_chat_message(
            browser_executable=resolve_browser_executable(
                parsed_arguments.browser_executable
            ),
            profile_directory=resolve_profile_directory(parsed_arguments.profile_dir),
            space_url=parsed_arguments.space_url,
            message_text=resolve_message_text(
                parsed_arguments.message, parsed_arguments.message_file
            ),
            headless=not parsed_arguments.headed,
            wait_seconds=parsed_arguments.wait_seconds,
            screenshot_path_argument=parsed_arguments.screenshot,
        )

    if parsed_arguments.command == "send-webhook":
        return send_google_chat_webhook_message(
            webhook_url=parsed_arguments.webhook_url,
            message_text=resolve_message_text(
                parsed_arguments.message, parsed_arguments.message_file
            ),
        )

    raise RuntimeError(f"Unsupported command: {parsed_arguments.command}")


def main() -> None:
    argument_parser = build_argument_parser()
    parsed_arguments = argument_parser.parse_args()

    try:
        command_result = run_command(parsed_arguments)
    except Exception as error:
        print(f"Error: {error}", file=sys.stderr)
        raise SystemExit(1) from None

    print(json.dumps(command_result, indent=2))


if __name__ == "__main__":
    main()
