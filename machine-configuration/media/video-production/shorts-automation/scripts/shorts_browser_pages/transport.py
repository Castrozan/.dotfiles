import json
from pathlib import Path
from urllib.request import Request, urlopen

from shorts_store import read_document


def create_page(server):
    configuration = read_document(Path.home() / ".pinchtab/config.json")
    request = Request(
        f"{server}/tab",
        data=json.dumps({"action": "new"}).encode(),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {configuration['server']['token']}",
        },
        method="POST",
    )
    with urlopen(request, timeout=15) as response:
        return json.load(response)["tabId"]
