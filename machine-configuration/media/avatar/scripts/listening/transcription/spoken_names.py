import re

WORD = re.compile(r"[^\W_]+")
NICKNAMES = {
    "Katsushika": ("Hokusai",),
    "Kingprotea": ("Protea",),
    "Ozymandias": ("Ozzy", "Ozzie"),
    "Quetzalcoatl": ("Quetzal",),
    "Scheherazade": ("Shera", "Shira"),
    "Ushiwakamaru": ("Ushiwaka",),
    "Xuanzang": ("Sanzang",),
}


def called_name(servant):
    return WORD.findall(servant)[0]


def answered_names(servant):
    called = called_name(servant)
    return (called, *NICKNAMES.get(called, ()))
