import urllib.error
import urllib.request


def http_request(method, url, headers, timeout_seconds=15, body=None):
    data = body.encode() if isinstance(body, str) else body
    request = urllib.request.Request(url, data=data, method=method)
    for header_name, header_value in headers.items():
        request.add_header(header_name, header_value)
    try:
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
            return response.status, response.read().decode()
    except urllib.error.HTTPError as error:
        return error.code, error.read().decode()
