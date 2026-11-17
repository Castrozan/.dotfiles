import json

import utterances


def print_status(directory, *, is_open, live, seat):
    report = {
        "open": is_open,
        "live": live,
        "seat": seat,
        "last_heard": utterances.last_heard(directory),
    }
    print(json.dumps(report))


def print_closed():
    print(json.dumps({"open": False}))
