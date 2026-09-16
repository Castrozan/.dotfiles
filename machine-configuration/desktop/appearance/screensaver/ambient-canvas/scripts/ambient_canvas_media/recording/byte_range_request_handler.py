import http.server
import os
import re

BYTE_RANGE_PATTERN = re.compile(r"^bytes=(\d*)-(\d*)$")


class ByteRangeLimitedReader:
    def __init__(self, opened_file, remaining_bytes):
        self.opened_file = opened_file
        self.remaining_bytes = remaining_bytes

    def read(self, requested_size=-1):
        if self.remaining_bytes <= 0:
            return b""
        if requested_size < 0 or requested_size > self.remaining_bytes:
            requested_size = self.remaining_bytes
        chunk = self.opened_file.read(requested_size)
        self.remaining_bytes -= len(chunk)
        return chunk

    def close(self):
        self.opened_file.close()


def resolve_requested_byte_range(range_header, total_size):
    if not range_header:
        return None
    matched_range = BYTE_RANGE_PATTERN.match(range_header.strip())
    if matched_range is None:
        return None
    first_text, last_text = matched_range.groups()
    if first_text:
        first_byte = int(first_text)
        last_byte = int(last_text) if last_text else total_size - 1
    else:
        if not last_text:
            return None
        first_byte = max(0, total_size - int(last_text))
        last_byte = total_size - 1
    last_byte = min(last_byte, total_size - 1)
    if first_byte > last_byte or first_byte >= total_size:
        return None
    return first_byte, last_byte


class ByteRangeRequestHandler(http.server.SimpleHTTPRequestHandler):
    def send_head(self):
        if self.headers.get("Range") is None:
            return super().send_head()
        requested_path = self.translate_path(self.path)
        if not os.path.isfile(requested_path):
            return super().send_head()
        total_size = os.path.getsize(requested_path)
        requested_range = resolve_requested_byte_range(
            self.headers.get("Range"), total_size
        )
        if requested_range is None:
            return super().send_head()
        first_byte, last_byte = requested_range
        opened_file = open(requested_path, "rb")
        opened_file.seek(first_byte)
        self.send_response(206)
        self.send_header("Content-Type", self.guess_type(requested_path))
        self.send_header("Accept-Ranges", "bytes")
        self.send_header(
            "Content-Range", f"bytes {first_byte}-{last_byte}/{total_size}"
        )
        self.send_header("Content-Length", str(last_byte - first_byte + 1))
        self.end_headers()
        return ByteRangeLimitedReader(opened_file, last_byte - first_byte + 1)
