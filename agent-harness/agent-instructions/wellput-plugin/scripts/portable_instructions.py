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
        if heading in (
            "### Peer communication",
            "### Artifact links",
            "### Exhaust before returning",
        ):
            continue
        if heading == "### Work in progress updates":
            section = section.partition("\n\nCore ")[0]
        if section.strip():
            selected.append(section.rstrip())
    return "\n\n".join(selected) + "\n"
