import re

WORD = re.compile(r"[^\W_]+")


def called_name(servant):
    return WORD.findall(servant)[0]
