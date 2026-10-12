import json
import os
from pathlib import Path

from memory_records import append_record
from staged_command import run_command


def probe_arguments(evaluation_flags):
    return [
        "nix",
        "--extra-experimental-features",
        "nix-command flakes",
        "eval",
        "--json",
        *evaluation_flags,
        "--offline",
        "--no-write-lock-file",
        "--no-eval-cache",
        "--option",
        "max-jobs",
        "0",
        "--option",
        "builders",
        "",
    ]


def measure_component(name, arguments, reference):
    phase = f"component_{name}"
    print(f"Measuring isolated component: {name}", flush=True)
    result = json.loads(
        run_command(phase, ["timeout", "--kill-after=5s", "600s", *arguments], True)
    )
    append_record(
        {
            "component": phase,
            "output_count": len(result) if isinstance(result, list) else 1,
            "reference": reference,
        }
    )


def component_application(public_reference, system, component):
    values = {
        "publicReference": public_reference,
        "system": system,
        "component": component,
    }
    encoded = json.dumps(json.dumps(values).replace("$", "\\u0024"))
    return f"component: component (builtins.fromJSON {encoded})"


def measure_components(
    public_reference, configuration_attribute, system, evaluation_flags
):
    append_record(
        {
            "sources": {
                "configuration": configuration_attribute,
                "public": public_reference,
            }
        }
    )
    os.environ["GC_INITIAL_HEAP_SIZE"] = "67108864"
    os.environ["GC_FREE_SPACE_DIVISOR"] = "8"
    configuration_probes = {
        "home_manager_activation": "configuration: map (user: user.home.activationPackage.drvPath) (builtins.attrValues configuration.home-manager.users)",
        "system_package_list": "configuration: map (package: package.drvPath) configuration.environment.systemPackages",
    }
    for name, expression in configuration_probes.items():
        measure_component(
            name,
            [
                *probe_arguments(evaluation_flags),
                configuration_attribute,
                "--apply",
                expression,
            ],
            configuration_attribute,
        )
    package_probes = ["devenv", "test_environment"]
    if system == "x86_64-linux":
        package_probes.append("latest_selected")
    for name in package_probes:
        measure_component(
            name,
            [
                *probe_arguments(()),
                "--file",
                str(Path(__file__).with_suffix(".nix")),
                "--apply",
                component_application(public_reference, system, name),
            ],
            public_reference,
        )
