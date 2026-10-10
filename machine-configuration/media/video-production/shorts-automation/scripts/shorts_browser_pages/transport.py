import json
from contextlib import closing
from http.client import HTTPConnection
from pathlib import Path
from urllib.parse import urlsplit

from shorts_store import read_document


def create_page(server):
    configuration = read_document(Path.home() / ".pinchtab/config.json")
    address = urlsplit(server)
    with closing(
        HTTPConnection(address.hostname, address.port, timeout=15)
    ) as connection:
        connection.request(
            "POST",
            "/tab",
            body=json.dumps({"action": "new"}).encode(),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {configuration['server']['token']}",
            },
        )
        with connection.getresponse() as response:
            if response.status >= 400:
                raise ValueError(
                    f"Browser page creation failed with HTTP {response.status}"
                )
            return json.load(response)["tabId"]
