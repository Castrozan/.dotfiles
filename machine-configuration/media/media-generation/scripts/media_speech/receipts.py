import json
import os
from pathlib import Path


RECEIPT_FILENAME = "receipt.json"


def write_receipt(directory: Path, receipt: dict):
    temporary_path = directory / "receipt.pending"
    with temporary_path.open("w", encoding="utf-8") as output:
        json.dump(receipt, output, ensure_ascii=False, allow_nan=False, indent=2)
        output.write("\n")
        output.flush()
        os.fsync(output.fileno())
    os.replace(temporary_path, directory / RECEIPT_FILENAME)
    directory_descriptor = os.open(directory, os.O_RDONLY)
    try:
        os.fsync(directory_descriptor)
    finally:
        os.close(directory_descriptor)
