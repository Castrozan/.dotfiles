import base64
import hmac
import json
import logging
from functools import partial
from http.server import BaseHTTPRequestHandler

from .domain import parse_event


class RequestFailure(Exception):
    def __init__(self, status):
        self.status = status


class WebhookHandler(BaseHTTPRequestHandler):
    def __init__(self, *arguments, ledger, authorization, wake_worker, **keywords):
        self.ledger = ledger
        self.authorization = authorization
        self.wake_worker = wake_worker
        super().__init__(*arguments, **keywords)

    def setup(self):
        super().setup()
        self.connection.settimeout(5)

    def reply(self, status):
        self.send_response(status)
        self.send_header("Content-Length", "0")
        self.end_headers()

    def application(self):
        if not hmac.compare_digest(
            self.headers.get("Authorization", "").encode(), self.authorization.encode()
        ):
            raise RequestFailure(401)
        app = self.path.removeprefix("/")
        if app not in ("radarr", "sonarr"):
            raise RequestFailure(404)
        return app

    def payload(self):
        length = int(self.headers.get("Content-Length", "0"))
        if not 0 < length <= 512 * 1024:
            raise RequestFailure(413)
        payload = json.loads(self.rfile.read(length))
        if not isinstance(payload, dict):
            raise ValueError("webhook must be an object")
        return payload

    def persist(self, app, payload):
        event = parse_event(app, payload)
        if event is None:
            return
        if event.kind == "download":
            self.ledger.record_download(event.media, event.download_hash)
        else:
            self.ledger.enqueue(event.media)
            logging.info("Queued cleanup for %s/%s", app, event.media.title)
        self.wake_worker.set()

    def do_POST(self):
        try:
            self.persist(self.application(), self.payload())
        except RequestFailure as error:
            self.reply(error.status)
        except (KeyError, TypeError, ValueError):
            self.reply(400)
        except Exception:
            logging.exception("Could not persist native webhook")
            self.reply(503)
        else:
            self.reply(200)

    def log_message(self, format, *arguments):
        logging.info("Webhook %s", format % arguments)


def webhook_handler(ledger, password, wake_worker):
    authorization = "Basic " + base64.b64encode(f"cleanup:{password}".encode()).decode()
    return partial(
        WebhookHandler,
        ledger=ledger,
        authorization=authorization,
        wake_worker=wake_worker,
    )
