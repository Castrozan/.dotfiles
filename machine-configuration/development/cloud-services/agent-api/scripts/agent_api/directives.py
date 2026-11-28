import json
from pathlib import Path

from agent_api.contract import CapabilityError
from agent_api.files import private_directory, write_json
from agent_api.inventory import LOCAL_HOST, host, hosts
from agent_api.providers.host_transport import host_command, run_on_host


def directive_catalog():
    return [
        {
            "id": "compute.placement",
            "description": "Host that runs compute.submit jobs when the request names none.",
            "targets": [entry["name"] for entry in hosts()],
            "default": LOCAL_HOST,
            "guidance": "Compute placement is {target}: submit long or heavy commands as agent-api compute jobs "
            "so they run on {target}.",
        }
    ]


def describe_directive(directive_id):
    directive = next(
        (entry for entry in directive_catalog() if entry["id"] == directive_id), None
    )
    if directive is None:
        raise CapabilityError("unsupported_directive")
    return directive


def propagate_choice(directive_id, target):
    propagated = {}
    for entry in hosts():
        if entry["transport"] != "ssh" or entry["trust"] != "owned":
            continue
        command = host_command(
            entry, ["agent-api", "direct", directive_id, target, "--no-propagate"]
        )
        try:
            run_on_host(command)
        except CapabilityError:
            propagated[entry["name"]] = False
        else:
            propagated[entry["name"]] = True
    return propagated


class DirectiveStore:
    def __init__(self, state_directory):
        self.path = Path(state_directory) / "directives.json"

    def chosen_targets(self):
        try:
            return json.loads(self.path.read_bytes())
        except FileNotFoundError:
            return {}

    def target(self, directive_id):
        directive = describe_directive(directive_id)
        target = self.chosen_targets().get(directive_id, directive["default"])
        if target not in directive["targets"]:
            raise CapabilityError("unsupported_target")
        return target

    def direct(self, directive_id, target, propagate=True):
        directive = describe_directive(directive_id)
        if target not in directive["targets"]:
            raise CapabilityError("unsupported_target")
        private_directory(self.path.parent)
        write_json(self.path, {**self.chosen_targets(), directive_id: target})
        directed = {**directive, "target": target}
        if not propagate:
            return directed
        return {**directed, "propagated": propagate_choice(directive_id, target)}

    def guidance_lines(self):
        return [
            directive["guidance"].format(target=self.target(directive["id"]))
            for directive in directive_catalog()
            if host(self.target(directive["id"]))["transport"] == "ssh"
        ]

    def listing(self):
        chosen_targets = self.chosen_targets()
        return [
            {
                **directive,
                "target": chosen_targets.get(directive["id"], directive["default"]),
            }
            for directive in directive_catalog()
        ]
