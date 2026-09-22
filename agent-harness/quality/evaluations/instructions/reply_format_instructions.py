import json
from pathlib import Path

from instructions.instruction_surface_scanner import REPO_ROOT


REPLY_FORMAT_PLACEHOLDER = "{{reply_format}}"
REPLY_FORMAT_CONFIGURATION_PATH = Path(
    "agent-harness/hooks/runtime/common/human_facing_reply/reply-formats.json"
)


def expand_reply_format_instructions(
    text: str, configuration: dict | None = None
) -> str:
    if REPLY_FORMAT_PLACEHOLDER not in text:
        return text
    if configuration is None:
        configuration = json.loads(
            (REPO_ROOT / REPLY_FORMAT_CONFIGURATION_PATH).read_text()
        )
    labels = configuration["formats"]["labeled_reply"]["labels"]
    emphasis = configuration["syntax"]["label_emphasis_marker"]
    values = {
        **configuration,
        "label_instructions": "\n\n".join(
            f"`{emphasis}{label['name'][0].upper() + label['name'][1:]}:{emphasis}` {label['instruction']}"
            for label in labels
        ),
        "label_budgets": "; ".join(
            f"{label['name']} {label['maximum_words']} + {label['grace_words']} words"
            for label in labels
        ),
    }
    instructions = "\n\n".join(
        paragraph.format_map(values)
        for paragraph in configuration["instruction_paragraphs"]
    )
    return text.replace(REPLY_FORMAT_PLACEHOLDER, instructions)
