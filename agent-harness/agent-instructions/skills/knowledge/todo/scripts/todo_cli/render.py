import json


def format_task_line(task):
    identifier = task.get("id", "?")
    content = task.get("content", "")
    due_text = _due_text(task.get("due"))
    label_text = _label_text(task.get("labels"))
    priority_text = _priority_text(task.get("priority", 1))
    return f"{identifier}  {content}{due_text}{label_text}{priority_text}"


def _due_text(due):
    if not due:
        return ""
    return f"  [due {due.get('date') or due.get('string') or ''}]"


def _label_text(labels):
    if not labels:
        return ""
    return "  " + " ".join("@" + label for label in labels)


def _priority_text(priority):
    if not priority or priority <= 1:
        return ""
    return f"  p{5 - priority}"


def emit_object(arguments, obj, human_text):
    if arguments.json:
        print(json.dumps(obj, ensure_ascii=False, indent=2))
    else:
        print(human_text)


def emit_tasks(arguments, tasks):
    if arguments.json:
        print(json.dumps(tasks, ensure_ascii=False, indent=2))
        return
    if not tasks:
        print("(no tasks)")
        return
    for task in tasks:
        print(format_task_line(task))


def render_digest_section(title, tasks):
    print(f"{title} ({len(tasks)})")
    for task in tasks:
        print("  " + format_task_line(task))
    print()
