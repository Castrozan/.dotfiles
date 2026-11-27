from pathlib import Path
import sys

import tomli_w


if __name__ == "__main__":
    instructions_path, output_path = map(Path, sys.argv[1:])
    instructions = instructions_path.read_bytes().decode()
    output_path.write_text(
        tomli_w.dumps({"developer_instructions": instructions}), encoding="utf-8"
    )
