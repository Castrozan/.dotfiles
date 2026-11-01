import functools
import http.server
import os


class FreshRendererHandler(http.server.SimpleHTTPRequestHandler):
    def send_head(self):
        del self.headers["If-Modified-Since"]
        return super().send_head()

    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()


def renderer_handler(directory):
    return functools.partial(FreshRendererHandler, directory=directory)


if __name__ == "__main__":
    http.server.ThreadingHTTPServer(
        ("127.0.0.1", 3000), renderer_handler(os.environ["AVATAR_RENDERER_ROOT"])
    ).serve_forever()
