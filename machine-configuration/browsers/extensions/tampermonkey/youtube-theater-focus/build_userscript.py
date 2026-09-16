import sys
from pathlib import Path


def build_userscript():
    source_directory = Path(__file__).resolve().parent
    sources = [
        "userscript-metadata.js",
        "hold-playback-until-focused.js",
        "theater-layout.js",
    ]
    return "\n".join((source_directory / name).read_text() for name in sources)


if __name__ == "__main__":
    sys.stdout.write(build_userscript())
