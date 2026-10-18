import re


def portable_skill(text):
    text = re.sub(
        r"Core\s+\[evidence\]\([^)]+\) owns "
        r"(?:verification and factual correction|epistemic judgment)\.",
        "",
        text,
    )
    return re.sub(r" under core\s+\[autonomy\]\([^)]+\)", "", text)


def portable_session_policy(text):
    sections = re.split(r"(?=^### )", text, flags=re.MULTILINE)
    selected = []
    for section in sections:
        heading = section.partition("\n")[0]
        if heading not in ("### Humanize policy loading", "### Response shape"):
            continue
        if section.strip():
            selected.append(section.rstrip())
    return "\n\n".join(selected) + "\n"
