CONSECUTIVE_TRANSIENT_FAILURE_LIMIT = 5
RETRY_PAUSE_SECONDS = 15


class ConsecutiveTransientFailures:
    def __init__(self, limit=CONSECUTIVE_TRANSIENT_FAILURE_LIMIT):
        self.limit = limit
        self.count = 0

    def record(self, description):
        self.count += 1
        if self.count >= self.limit:
            raise RuntimeError(f"{description}, {self.count} times in a row")

    def reset(self):
        self.count = 0
