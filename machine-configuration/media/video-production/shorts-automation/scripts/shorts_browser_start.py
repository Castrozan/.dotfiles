import os
import time

from shorts_browser import browser_instance
from shorts_store import read_document


def main():
    configuration = read_document(os.environ["SHORTS_CONFIGURATION"])
    for _ in range(45):
        try:
            browser_instance(configuration)
            return
        except (ValueError, OSError):
            time.sleep(1)
    raise ValueError("The exact Shorts browser did not become ready")


if __name__ == "__main__":
    main()
