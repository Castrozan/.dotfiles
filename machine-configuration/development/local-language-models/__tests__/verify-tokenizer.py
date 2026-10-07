import json
import subprocess
import sys

tokenizer, vocabulary = sys.argv[1:]
cases = [
    ("x" * 51200, [44102] * 6400),
    ("hello world", [14990, 1879]),
    (
        "café a\u0301 can't 123\n世界",
        [924, 58858, 264, 53839, 646, 944, 220, 16, 17, 18, 198, 99489],
    ),
]

for text, expected in cases:
    result = subprocess.run(
        [tokenizer, "-m", vocabulary, "--ids", "--log-disable", "--no-bos", "--stdin"],
        input=text,
        capture_output=True,
        text=True,
        timeout=15,
        check=True,
    )
    actual = json.loads(result.stdout)
    assert actual == expected, (len(text), len(actual), len(expected))

print("Qwen3.5 tokenizer handles long letter runs and preserves mixed Unicode tokens")
