import json
import os
import subprocess
import sys
from pathlib import Path

cli = os.environ["OPENCLI_CLI"]
url, output = sys.argv[1:3]
output = Path(output)


def action(*arguments, session="proof"):
    result = subprocess.run(
        [cli, "browser", *arguments, "--session", session],
        check=False,
        capture_output=True,
        text=True,
        timeout=40,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    envelope = json.loads(result.stdout)
    assert envelope["ok"] is True, envelope
    return envelope["data"]


checks = {}
action("open", url)
if sys.argv[3:] == ["--persist"]:
    assert action("eval", "localStorage.getItem('opencli-proof')") == "retained"
    print(json.dumps({"profile_persists_across_cold_starts": True}))
    sys.exit(0)
checks["structured_snapshot"] = "OpenCLI proof" in json.dumps(action("state"))
action("fill", "#name", "Lucas")
action("click", "#load")
action("wait", "text", "Lucas: 3 items")
checks["native_form_interaction"] = (
    action("eval", "document.querySelector('#result').textContent") == "Lucas: 3 items"
)
checks["markdown_extraction"] = "OpenCLI proof" in json.dumps(
    action("extract", "--selector", "main")
)
network = action("network", "--static")
checks["network_and_endpoint_discovery"] = "api/items" in json.dumps(network)
video = output / "fixture.mp4"
video.write_bytes(b"upload-fixture")
action("upload", "#upload", str(video))
checks["local_file_attachment"] = (
    action("eval", "document.querySelector('#upload').files[0].name") == "fixture.mp4"
)
second = action("tab", "new", session="second")["page"]
tabs = action("tab", "list")
second_tabs = action("tab", "list", session="second")
checks["independent_owned_sessions"] = (
    len(tabs) == 1
    and len(second_tabs) == 1
    and tabs[0]["page"] != second_tabs[0]["page"]
)
action("tab", "close", second, session="second")
action("eval", "localStorage.setItem('opencli-proof', 'retained'); true")
action("screenshot", str(output / "proof.png"))
checks["screenshot"] = (
    (output / "proof.png").read_bytes().startswith(bytes.fromhex("89504e470d0a1a0a"))
)
article = subprocess.run(
    [
        cli,
        "web",
        "read",
        "--url",
        "https://github.com/jackwener/OpenCLI",
        "--stdout",
        "true",
        "--download-images",
        "false",
        "--wait",
        "1",
    ],
    capture_output=True,
    text=True,
    timeout=60,
)
checks["real_web_article_adapter"] = (
    article.returncode == 0
    and "OpenCLI" in article.stdout
    and len(article.stdout) > 500
)
assert all(checks.values()), checks
print(json.dumps(checks))
