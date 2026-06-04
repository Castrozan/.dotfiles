from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
CORE_INSTRUCTIONS_PATH = REPO_ROOT / "agents" / "core_rules" / "core.md"


def load_core_instructions_body() -> str:
    content = CORE_INSTRUCTIONS_PATH.read_text()
    parts = content.split("---", 2)
    if len(parts) >= 3:
        return parts[2].strip()
    return content.strip()


def load_core_instructions_with_frontmatter() -> str:
    return CORE_INSTRUCTIONS_PATH.read_text()


UNPROMPTED_SCENARIOS = [
    {
        "name": "edit_without_instruction_hints",
        "description": (
            "Edit task with NO mention of reading first, "
            "no comments, or naming conventions"
        ),
        "files": {
            "src/handler.py": (
                "def proc(d):\n"
                "    r = []\n"
                "    for i in d:\n"
                "        if i > 0:\n"
                "            r.append(i * 2)\n"
                "    return r\n"
            ),
        },
        "prompt": ("Refactor src/handler.py to be cleaner and more readable."),
    },
    {
        "name": "bug_fix_without_methodology_hints",
        "description": (
            "Bug fix with NO mention of investigating or reading files first"
        ),
        "files": {
            "app/service.py": (
                "from app.db import get_item\n\n"
                "def calculate_total(order_id):\n"
                "    items = get_item(order_id)\n"
                "    return sum(i['price'] for i in items)\n"
            ),
            "app/db.py": (
                "DATA = {\n"
                '    1: [{"name": "A", "price": 10}],\n'
                '    2: [{"name": "B", "price": 20}],\n'
                "}\n\n"
                "def get_item(order_id):\n"
                "    return DATA[order_id]\n"
            ),
        },
        "prompt": (
            "calculate_total crashes with KeyError when order_id is 999. Fix it."
        ),
    },
    {
        "name": "find_files_without_tool_hints",
        "description": ("File search with NO mention of which tool to use"),
        "files": {
            "src/main.py": 'print("hello")\n',
            "src/utils.py": "def helper(): pass\n",
            "lib/core.py": "class Core: pass\n",
            "tests/test_main.py": ("def test_main(): assert True\n"),
        },
        "prompt": ("What Python files exist in this project? List them."),
    },
]
