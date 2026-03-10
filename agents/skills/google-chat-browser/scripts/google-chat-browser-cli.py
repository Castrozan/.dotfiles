from __future__ import annotations

import argparse
import json
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

pinchtab_base_url = "http://localhost:9867"
default_google_chat_home_url = "https://chat.google.com/"
default_navigation_wait_seconds = 30

google_sign_in_url_pattern = re.compile(
    r"accounts\.google\.com|ServiceLogin", re.IGNORECASE
)
google_chat_url_pattern = re.compile(r"^https://chat\.google\.com/", re.IGNORECASE)
message_composer_snapshot_pattern = re.compile(
    r"send a message|enviar uma mensagem|message to|mensagem para",
    re.IGNORECASE,
)
send_button_snapshot_pattern = re.compile(
    r"^(send|enviar)(\s+(message|mensagem))?$", re.IGNORECASE
)
snapshot_element_ref_pattern = re.compile(r"^(e\d+):")


def print_log_message(message: str) -> None:
    print(message, file=sys.stderr)


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


def pinchtab_http_request(
    endpoint: str,
    method: str = "GET",
    payload: dict | None = None,
    timeout: int = 60,
) -> str:
    url = f"{pinchtab_base_url}{endpoint}"
    request_data = json.dumps(payload).encode("utf-8") if payload else None
    headers = {"Content-Type": "application/json"} if request_data else {}

    request = urllib.request.Request(
        url, data=request_data, headers=headers, method=method
    )

    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return response.read().decode("utf-8")
    except urllib.error.HTTPError as error:
        error_body = error.read().decode("utf-8").strip()
        raise RuntimeError(
            f"Pinchtab {endpoint} failed (HTTP {error.code}): {error_body}"
        ) from None
    except urllib.error.URLError as error:
        raise RuntimeError(
            f"Cannot reach pinchtab at {pinchtab_base_url}. "
            f"Ensure it is running: {error.reason}"
        ) from None


def pinchtab_json_request(
    endpoint: str,
    method: str = "GET",
    payload: dict | None = None,
    timeout: int = 60,
) -> dict:
    response_body = pinchtab_http_request(endpoint, method, payload, timeout)
    if not response_body.strip():
        return {}
    return json.loads(response_body)


def ensure_pinchtab_is_healthy() -> None:
    health = pinchtab_json_request("/health", timeout=5)
    if health.get("status") != "ok":
        raise RuntimeError(
            f"Pinchtab health check returned unexpected status: {health}"
        )


def navigate_pinchtab_to_url(destination_url: str) -> None:
    print_log_message(f"Opening {destination_url}")
    pinchtab_http_request(
        "/navigate", method="POST", payload={"url": destination_url}, timeout=15
    )


def get_pinchtab_interactive_snapshot() -> str:
    return pinchtab_http_request(
        "/snapshot?filter=interactive&format=compact", timeout=15
    )


def get_pinchtab_minimal_snapshot() -> str:
    return pinchtab_http_request("/snapshot?format=compact&depth=0", timeout=15)


def get_pinchtab_diff_snapshot() -> str:
    return pinchtab_http_request("/snapshot?diff=true&format=compact", timeout=15)


def perform_pinchtab_action(action_payload: dict) -> None:
    pinchtab_http_request("/action", method="POST", payload=action_payload, timeout=10)


def evaluate_javascript_in_pinchtab(expression: str) -> str:
    result = pinchtab_json_request(
        "/evaluate", method="POST", payload={"expression": expression}, timeout=15
    )
    return str(result.get("result", ""))


def extract_url_from_snapshot_header(snapshot_text: str) -> str:
    first_line = snapshot_text.split("\n", 1)[0]
    parts = first_line.split(" | ")
    if len(parts) >= 2:
        return parts[1]
    return ""


def extract_title_from_snapshot_header(snapshot_text: str) -> str:
    first_line = snapshot_text.split("\n", 1)[0]
    if first_line.startswith("# "):
        return first_line.split(" | ", 1)[0][2:]
    return ""


def wait_for_pinchtab_page_to_stabilize(
    max_wait_seconds: float = 5.0,
) -> None:
    poll_interval = 0.3
    elapsed = 0.0
    previous_snapshot = ""

    time.sleep(1)

    while elapsed < max_wait_seconds:
        current_snapshot = get_pinchtab_diff_snapshot()
        if previous_snapshot and current_snapshot == previous_snapshot:
            return
        previous_snapshot = current_snapshot
        time.sleep(poll_interval)
        elapsed += poll_interval


def raise_if_google_sign_in_required(current_url: str) -> None:
    if google_sign_in_url_pattern.search(current_url):
        raise RuntimeError(
            "Google sign-in is required. Log in via pinchtab headed mode first:\n"
            "  pinchtab-switch-mode headed\n"
            "  pinchtab-navigate-and-snapshot 'https://chat.google.com/'\n"
            "  # Complete login in the browser window\n"
            "  pinchtab-switch-mode headless"
        )


def navigate_and_wait_for_google_chat(destination_url: str, wait_seconds: int) -> str:
    navigate_pinchtab_to_url(destination_url)
    wait_for_pinchtab_page_to_stabilize()

    deadline = time.time() + wait_seconds

    while time.time() < deadline:
        snapshot_text = get_pinchtab_minimal_snapshot()
        current_url = extract_url_from_snapshot_header(snapshot_text)

        if google_chat_url_pattern.search(
            current_url
        ) and not google_sign_in_url_pattern.search(current_url):
            return snapshot_text

        raise_if_google_sign_in_required(current_url)
        time.sleep(1)

    raise RuntimeError("Google Chat did not become ready before the timeout")


def find_element_ref_in_snapshot(
    snapshot_text: str,
    element_type: str,
    label_pattern: re.Pattern,
    skip_disabled: bool = False,
) -> str | None:
    type_marker = f":{element_type} "

    for line in snapshot_text.splitlines():
        if type_marker not in line:
            continue

        if skip_disabled and line.rstrip().endswith(" -"):
            continue

        label_start = line.find(type_marker) + len(type_marker)
        label_text = line[label_start:].strip().strip('"')
        if label_pattern.search(label_text):
            ref_match = snapshot_element_ref_pattern.match(line)
            if ref_match:
                return ref_match.group(1)

    return None


def wait_for_message_composer_ref(wait_seconds: int) -> str:
    deadline = time.time() + wait_seconds

    while time.time() < deadline:
        snapshot_text = get_pinchtab_interactive_snapshot()
        current_url = extract_url_from_snapshot_header(snapshot_text)
        raise_if_google_sign_in_required(current_url)

        composer_ref = find_element_ref_in_snapshot(
            snapshot_text, "textbox", message_composer_snapshot_pattern
        )
        if composer_ref:
            return composer_ref
        time.sleep(1)

    raise RuntimeError(
        "Message composer not found. Check the target space URL and login session"
    )


def fill_composer_with_message_via_javascript(message_text: str) -> None:
    escaped_message_json = json.dumps(message_text)
    javascript_fill_expression = (
        "(function() {"
        "  var composer = document.querySelector("
        '    \'div[contenteditable="true"][role="textbox"]\''
        "  );"
        '  if (!composer) return "composer_not_found";'
        "  composer.focus();"
        "  var selection = window.getSelection();"
        "  var range = document.createRange();"
        "  range.selectNodeContents(composer);"
        "  selection.removeAllRanges();"
        "  selection.addRange(range);"
        "  document.execCommand('delete');"
        f"  document.execCommand('insertText', false, {escaped_message_json});"
        '  return "filled";'
        "})()"
    )

    result = evaluate_javascript_in_pinchtab(javascript_fill_expression)
    if "composer_not_found" in result:
        raise RuntimeError("Could not find the message composer element in the DOM")
    if "filled" not in result:
        raise RuntimeError(f"Unexpected result from composer fill: {result}")


def wait_for_send_button_and_click(wait_seconds: int) -> None:
    deadline = time.time() + wait_seconds

    while time.time() < deadline:
        snapshot_text = get_pinchtab_interactive_snapshot()
        send_ref = find_element_ref_in_snapshot(
            snapshot_text, "button", send_button_snapshot_pattern, skip_disabled=True
        )
        if send_ref:
            perform_pinchtab_action({"kind": "click", "ref": send_ref})
            return
        time.sleep(0.5)

    raise RuntimeError("Send button not found or not enabled")


def wait_for_composer_to_clear(wait_seconds: int) -> None:
    deadline = time.time() + wait_seconds

    while time.time() < deadline:
        result = evaluate_javascript_in_pinchtab(
            "(function() {"
            "  var c = document.querySelector("
            '    \'div[contenteditable="true"][role="textbox"]\''
            "  );"
            "  if (!c) return 'gone';"
            "  return (c.innerText || '').trim() === '' ? 'empty' : 'has_text';"
            "})()"
        )
        if "empty" in result or "gone" in result:
            return
        time.sleep(0.5)

    print_log_message("Warning: message dispatch verification timed out")


def login_to_google_chat(
    destination_url: str,
    wait_seconds: int,
) -> dict[str, object]:
    ensure_pinchtab_is_healthy()
    print_log_message(
        "Login uses pinchtab's browser session. If not logged in:\n"
        "  1. Run: pinchtab-switch-mode headed\n"
        "  2. Complete Google sign-in in the browser window\n"
        "  3. Run: pinchtab-switch-mode headless"
    )

    navigate_pinchtab_to_url(destination_url)
    wait_for_pinchtab_page_to_stabilize()

    snapshot_text = get_pinchtab_minimal_snapshot()
    current_url = extract_url_from_snapshot_header(snapshot_text)
    page_title = extract_title_from_snapshot_header(snapshot_text)

    signed_in = bool(
        google_chat_url_pattern.search(current_url)
        and not google_sign_in_url_pattern.search(current_url)
    )

    return {
        "success": signed_in,
        "mode": "login",
        "url": current_url,
        "title": page_title,
        "backend": "pinchtab",
        "signed_in": signed_in,
    }


def get_google_chat_session_status(
    wait_seconds: int,
) -> dict[str, object]:
    ensure_pinchtab_is_healthy()
    snapshot_text = navigate_and_wait_for_google_chat(
        default_google_chat_home_url, wait_seconds
    )
    current_url = extract_url_from_snapshot_header(snapshot_text)
    page_title = extract_title_from_snapshot_header(snapshot_text)

    return {
        "success": True,
        "mode": "session-status",
        "url": current_url,
        "title": page_title,
        "backend": "pinchtab",
    }


def detect_image_mime_type_from_path(image_path: Path) -> str:
    extension_to_mime_type = {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".gif": "image/gif",
        ".webp": "image/webp",
        ".bmp": "image/bmp",
    }
    mime_type = extension_to_mime_type.get(image_path.suffix.lower())
    if not mime_type:
        raise RuntimeError(
            f"Unsupported image format: {image_path.suffix}. "
            f"Supported: {', '.join(extension_to_mime_type.keys())}"
        )
    return mime_type


def read_image_as_base64(image_path: Path) -> tuple[str, str]:
    resolved_path = image_path.expanduser().resolve()
    if not resolved_path.is_file():
        raise RuntimeError(f"Image file not found: {resolved_path}")

    mime_type = detect_image_mime_type_from_path(resolved_path)
    import base64

    image_bytes = resolved_path.read_bytes()
    base64_encoded = base64.b64encode(image_bytes).decode("ascii")
    return base64_encoded, mime_type


def paste_image_into_composer_via_javascript(image_path: Path) -> None:
    print_log_message(f"Injecting image into composer: {image_path.name}")
    base64_data, mime_type = read_image_as_base64(image_path)
    filename = image_path.name

    javascript_paste_expression = (
        "(function(){"
        f'var b64="{base64_data}";'
        "var raw=atob(b64);"
        "var arr=new Uint8Array(raw.length);"
        "for(var i=0;i<raw.length;i++)arr[i]=raw.charCodeAt(i);"
        f'var blob=new Blob([arr],{{type:"{mime_type}"}});'
        f'var file=new File([blob],"{filename}",{{type:"{mime_type}"}});'
        "var dt=new DataTransfer();"
        "dt.items.add(file);"
        "var composer=document.querySelector("
        '\'div[contenteditable="true"][role="textbox"]\''
        ");"
        'if(!composer)return"no_composer";'
        "composer.focus();"
        'var pe=new ClipboardEvent("paste",{'
        "bubbles:true,cancelable:true,clipboardData:dt});"
        "composer.dispatchEvent(pe);"
        'return"pasted";'
        "})()"
    )

    result = evaluate_javascript_in_pinchtab(javascript_paste_expression)
    if "no_composer" in result:
        raise RuntimeError("Could not find the message composer element in the DOM")
    if "pasted" not in result:
        raise RuntimeError(f"Unexpected result from image paste: {result}")


def wait_for_send_button_after_image_paste(wait_seconds: int) -> None:
    deadline = time.time() + wait_seconds

    while time.time() < deadline:
        snapshot_text = get_pinchtab_interactive_snapshot()
        send_ref = find_element_ref_in_snapshot(
            snapshot_text, "button", send_button_snapshot_pattern, skip_disabled=True
        )
        if send_ref:
            return
        time.sleep(0.5)

    raise RuntimeError("Send button did not appear after pasting image")


def send_google_chat_message(
    space_url: str,
    message_text: str,
    wait_seconds: int,
    image_path: str | None = None,
) -> dict[str, object]:
    ensure_pinchtab_is_healthy()
    navigate_and_wait_for_google_chat(space_url, wait_seconds)
    composer_ref = wait_for_message_composer_ref(wait_seconds)
    perform_pinchtab_action({"kind": "click", "ref": composer_ref})
    time.sleep(0.5)

    if image_path:
        paste_image_into_composer_via_javascript(Path(image_path))
        time.sleep(1)
        wait_for_send_button_after_image_paste(wait_seconds)

    fill_composer_with_message_via_javascript(message_text)
    time.sleep(0.3)

    print_log_message("Sending message")
    wait_for_send_button_and_click(wait_seconds)
    wait_for_composer_to_clear(wait_seconds)

    snapshot_text = get_pinchtab_minimal_snapshot()
    current_url = extract_url_from_snapshot_header(snapshot_text)
    page_title = extract_title_from_snapshot_header(snapshot_text)

    result: dict[str, object] = {
        "success": True,
        "mode": "browser",
        "space_url": current_url,
        "title": page_title,
        "backend": "pinchtab",
        "message_length": len(message_text),
        "message_preview": create_message_preview(message_text),
    }
    if image_path:
        result["image"] = image_path
    return result


def send_google_chat_image(
    space_url: str,
    image_path: str,
    caption_text: str | None,
    wait_seconds: int,
) -> dict[str, object]:
    ensure_pinchtab_is_healthy()
    navigate_and_wait_for_google_chat(space_url, wait_seconds)
    composer_ref = wait_for_message_composer_ref(wait_seconds)
    perform_pinchtab_action({"kind": "click", "ref": composer_ref})
    time.sleep(0.5)

    paste_image_into_composer_via_javascript(Path(image_path))
    time.sleep(1)
    wait_for_send_button_after_image_paste(wait_seconds)

    if caption_text:
        fill_composer_with_message_via_javascript(caption_text)
        time.sleep(0.3)

    print_log_message("Sending image")
    wait_for_send_button_and_click(wait_seconds)
    time.sleep(1)

    snapshot_text = get_pinchtab_minimal_snapshot()
    current_url = extract_url_from_snapshot_header(snapshot_text)
    page_title = extract_title_from_snapshot_header(snapshot_text)

    result: dict[str, object] = {
        "success": True,
        "mode": "browser",
        "space_url": current_url,
        "title": page_title,
        "backend": "pinchtab",
        "image": image_path,
    }
    if caption_text:
        result["caption_length"] = len(caption_text)
        result["caption_preview"] = create_message_preview(caption_text)
    return result


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
            "Send Google Chat messages through pinchtab browser session or webhook."
        ),
    )
    subcommands = argument_parser.add_subparsers(dest="command", required=True)

    login_subcommand = subcommands.add_parser(
        "login",
        help="Check pinchtab session or show login instructions.",
    )
    login_subcommand.add_argument(
        "--space-url",
        default=default_google_chat_home_url,
    )
    login_subcommand.add_argument("--headed", action="store_true")
    login_subcommand.add_argument(
        "--wait-seconds",
        type=int,
        default=default_navigation_wait_seconds,
    )
    login_subcommand.add_argument("--profile-dir")
    login_subcommand.add_argument("--browser-executable")
    login_subcommand.add_argument("--screenshot")

    session_status_subcommand = subcommands.add_parser(
        "session-status",
        help="Check whether the pinchtab Google Chat session is ready.",
    )
    session_status_subcommand.add_argument(
        "--wait-seconds",
        type=int,
        default=default_navigation_wait_seconds,
    )
    session_status_subcommand.add_argument("--profile-dir")
    session_status_subcommand.add_argument("--browser-executable")
    session_status_subcommand.add_argument("--screenshot")

    send_message_subcommand = subcommands.add_parser(
        "send-message",
        help="Send a message to a Google Chat space or DM.",
    )
    send_message_subcommand.add_argument("--space-url", required=True)
    send_message_subcommand.add_argument("--message")
    send_message_subcommand.add_argument("--message-file")
    send_message_subcommand.add_argument("--image")
    send_message_subcommand.add_argument(
        "--wait-seconds",
        type=int,
        default=default_navigation_wait_seconds,
    )
    send_message_subcommand.add_argument("--headed", action="store_true")
    send_message_subcommand.add_argument("--profile-dir")
    send_message_subcommand.add_argument("--browser-executable")
    send_message_subcommand.add_argument("--screenshot")

    send_image_subcommand = subcommands.add_parser(
        "send-image",
        help="Send an image to a Google Chat space or DM via clipboard paste.",
    )
    send_image_subcommand.add_argument("--space-url", required=True)
    send_image_subcommand.add_argument("--image", required=True)
    send_image_subcommand.add_argument("--caption")
    send_image_subcommand.add_argument(
        "--wait-seconds",
        type=int,
        default=default_navigation_wait_seconds,
    )

    send_webhook_subcommand = subcommands.add_parser(
        "send-webhook",
        help="Send a message to an existing Google Chat incoming webhook.",
    )
    send_webhook_subcommand.add_argument("--webhook-url", required=True)
    send_webhook_subcommand.add_argument("--message")
    send_webhook_subcommand.add_argument("--message-file")

    return argument_parser


def run_command(parsed_arguments: argparse.Namespace) -> dict[str, object]:
    if parsed_arguments.command == "login":
        return login_to_google_chat(
            destination_url=parsed_arguments.space_url,
            wait_seconds=parsed_arguments.wait_seconds,
        )

    if parsed_arguments.command == "session-status":
        return get_google_chat_session_status(
            wait_seconds=parsed_arguments.wait_seconds,
        )

    if parsed_arguments.command == "send-message":
        return send_google_chat_message(
            space_url=parsed_arguments.space_url,
            message_text=resolve_message_text(
                parsed_arguments.message, parsed_arguments.message_file
            ),
            wait_seconds=parsed_arguments.wait_seconds,
            image_path=getattr(parsed_arguments, "image", None),
        )

    if parsed_arguments.command == "send-image":
        return send_google_chat_image(
            space_url=parsed_arguments.space_url,
            image_path=parsed_arguments.image,
            caption_text=parsed_arguments.caption,
            wait_seconds=parsed_arguments.wait_seconds,
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
