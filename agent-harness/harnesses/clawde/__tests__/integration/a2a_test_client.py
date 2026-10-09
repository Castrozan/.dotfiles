import http.client
import json


def request_json(fleet, method, path, document=None):
    connection = http.client.HTTPConnection(
        fleet.endpoint.removeprefix("http://"), timeout=5
    )
    try:
        body = None if document is None else json.dumps(document).encode()
        connection.request(
            method, path, body=body, headers={"Content-Type": "application/json"}
        )
        response = connection.getresponse()
        return response.status, json.loads(response.read())
    finally:
        connection.close()
