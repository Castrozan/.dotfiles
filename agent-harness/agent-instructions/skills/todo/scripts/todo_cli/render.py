import json


def format_task_line(task):
    identifier = task.get("id", "?")
    content = task.get("content", "")
    due = task.get("due")
    due_text = f"  [due {due.get('date') or due.get('string') or ''}]" if due else ""
    labels = task.get("labels") or []
    label_text = "  " + " ".join("@" + label for label in labels) if labels else ""
    priority = task.get("priority", 1)
    priority_text = f"  p{5 - priority}" if priority and priority > 1 else ""
    return f"{identifier}  {content}{due_text}{label_text}{priority_text}"


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
