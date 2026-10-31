import functools
import http.server
import os


handler = functools.partial(
    http.server.SimpleHTTPRequestHandler, directory=os.environ["AVATAR_RENDERER_ROOT"]
)
http.server.ThreadingHTTPServer(("127.0.0.1", 3000), handler).serve_forever()
