import json

from api import fetch_paginated, resolve_project_id, send_request
from render import emit_object, emit_tasks, render_digest_section


def command_add(arguments, token):
    body = {"content": arguments.content}
    if arguments.due:
        body["due_string"] = arguments.due
    if arguments.priority:
        body["priority"] = arguments.priority
    if arguments.label:
        body["labels"] = arguments.label
    if arguments.description:
        body["description"] = arguments.description
    if arguments.project:
        body["project_id"] = resolve_project_id(arguments.project, token)
    task = send_request("POST", "/tasks", token, body=body)
    emit_object(arguments, task, f"added {task['id']}: {task['content']}")


def command_list(arguments, token):
    if arguments.filter:
        tasks = fetch_paginated(
            "/tasks/filter", token, query={"query": arguments.filter}
        )
    else:
        tasks = fetch_paginated("/tasks", token)
    emit_tasks(arguments, tasks)


def command_digest(arguments, token):
    overdue = fetch_paginated("/tasks/filter", token, query={"query": "overdue"})
    today = fetch_paginated("/tasks/filter", token, query={"query": "today"})
    someday = fetch_paginated("/tasks/filter", token, query={"query": "no date"})
    if arguments.json:
        grouped = {"overdue": overdue, "today": today, "someday": someday}
        print(json.dumps(grouped, ensure_ascii=False, indent=2))
        return
    render_digest_section("Overdue", overdue)
    render_digest_section("Today", today)
    render_digest_section("Someday", someday)


def command_done(arguments, token):
    send_request("POST", f"/tasks/{arguments.id}/close", token)
    print(f"completed {arguments.id}")


def command_reopen(arguments, token):
    send_request("POST", f"/tasks/{arguments.id}/reopen", token)
    print(f"reopened {arguments.id}")


def command_delete(arguments, token):
    send_request("DELETE", f"/tasks/{arguments.id}", token)
    print(f"deleted {arguments.id}")


def command_update(arguments, token):
    body = {}
    if arguments.content:
        body["content"] = arguments.content
    if arguments.due:
        body["due_string"] = arguments.due
    if arguments.priority:
        body["priority"] = arguments.priority
    if arguments.label:
        body["labels"] = arguments.label
    if arguments.description is not None:
        body["description"] = arguments.description
    if not body:
        raise SystemExit("update needs at least one field to change")
    task = send_request("POST", f"/tasks/{arguments.id}", token, body=body)
    emit_object(arguments, task or {"id": arguments.id}, f"updated {arguments.id}")


def command_projects(arguments, token):
    projects = fetch_paginated("/projects", token)
    if arguments.json:
        print(json.dumps(projects, ensure_ascii=False, indent=2))
        return
    for project in projects:
        print(f"{project['id']}  {project['name']}")
