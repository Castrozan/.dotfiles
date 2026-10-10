from http.client import HTTPConnection
from http.cookies import SimpleCookie
from urllib.parse import urlsplit


class HttpFailure(RuntimeError):
    def __init__(self, status):
        super().__init__(f"Application request failed with HTTP {status}")
        self.status = status


class HttpTransport:
    def __init__(self, base_url, headers):
        address = urlsplit(base_url)
        if address.scheme != "http" or not address.hostname:
            raise ValueError("cleanup accepts only explicit HTTP application addresses")
        self.address = address
        self.headers = headers
        self.cookie = ""

    def request(self, path, method="GET", data=None):
        connection = HTTPConnection(self.address.hostname, self.address.port, timeout=5)
        try:
            connection.request(
                method,
                self.address.path + path,
                body=data,
                headers={**self.headers, "Cookie": self.cookie},
            )
            response = connection.getresponse()
            self.remember_cookie(response)
            body = response.read(16 * 1024 * 1024 + 1)
            if len(body) > 16 * 1024 * 1024:
                raise ValueError("application response exceeds size limit")
            if response.status >= 400:
                raise HttpFailure(response.status)
            return body
        finally:
            connection.close()

    def remember_cookie(self, response):
        header = response.getheader("Set-Cookie")
        if header:
            cookies = SimpleCookie(header)
            self.cookie = "; ".join(
                f"{name}={value.value}" for name, value in cookies.items()
            )
