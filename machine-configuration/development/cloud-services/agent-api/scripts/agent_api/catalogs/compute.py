from agent_api.catalogs.local import capability, object_schema, text

JOB = text(36)


def submit_capability():
    return capability(
        "compute.submit",
        "systemd",
        "Start a command as a resource-limited systemd user unit on a compute host and return at once; "
        "the host defaults to the compute.placement directive and the returned job feeds status, logs and cancel.",
        object_schema(
            {
                "command": {
                    "type": "array",
                    "minItems": 1,
                    "maxItems": 64,
                    "items": {"type": "string", "maxLength": 4096},
                },
                "host": text(63),
                "directory": text(),
                "memory_megabytes": {
                    "type": "integer",
                    "minimum": 64,
                    "maximum": 65536,
                    "default": 2048,
                },
                "cpu_percent": {
                    "type": "integer",
                    "minimum": 10,
                    "maximum": 6400,
                    "default": 100,
                },
                "runtime_seconds": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 86400,
                    "default": 3600,
                },
            },
            ["command"],
        ),
    )


def compute_capabilities():
    return [
        capability(
            "compute.hosts",
            "systemd",
            "List compute hosts with their system, size and trust tier; contacts no host.",
            object_schema({}, []),
        ),
        {
            **submit_capability(),
            "directive": {"id": "compute.placement", "input": "host"},
        },
        capability(
            "compute.status",
            "systemd",
            "Report whether a submitted job is running, succeeded, failed or unknown, with its exit code.",
            object_schema({"job": JOB}, ["job"]),
        ),
        capability(
            "compute.logs",
            "systemd",
            "Return the most recent output lines of a submitted job from its host's journal.",
            object_schema(
                {
                    "job": JOB,
                    "lines": {
                        "type": "integer",
                        "minimum": 1,
                        "maximum": 2000,
                        "default": 200,
                    },
                },
                ["job"],
            ),
        ),
        capability(
            "compute.cancel",
            "systemd",
            "Stop a submitted job and release its unit; a finished job stays inspectable until cancelled.",
            object_schema({"job": JOB}, ["job"]),
        ),
    ]
