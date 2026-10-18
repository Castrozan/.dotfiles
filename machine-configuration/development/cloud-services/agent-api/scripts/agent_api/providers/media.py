import json
import shutil
from pathlib import Path

from agent_api.contract import MAXIMUM_ARTIFACT_BYTES, CapabilityError
from agent_api.files import file_digest, input_file, write_json
from agent_api.providers.processing import run_tool, tool


class MediaProvider:
    def preflight(self, request):
        pass

    def execute(self, request, directory, operation_id):
        if request.capability == "media.providers":
            command = [tool("media-" + request.input["kind"]), "providers"]
        elif request.capability == "movie.schema":
            command = [tool("media-movie"), "schema"]
        else:
            kind, action = request.capability.split(".")
            command = [tool("media-" + kind), action]
            if kind in ("movie", "video"):
                data = {**request.input["request"], "operation_id": operation_id}
                path = directory / "media-request.json"
                write_json(path, data)
                command.extend(["--request-file", str(path)])
            else:
                command.extend(["--operation-id", operation_id])
                for name, value in request.input.items():
                    command.extend(["--" + name.replace("_", "-"), str(value)])
        discovery = request.capability in ("media.providers", "movie.schema")
        if not discovery:
            write_json(
                directory / "submission.json",
                {
                    "provider": "media",
                    "operation_id": operation_id,
                    "command": command[0],
                },
            )
        result = json.loads(run_tool(command, directory, request.timeout_seconds))
        if discovery:
            return result
        if result.get("status") != "succeeded":
            raise CapabilityError("media_operation_failed")
        self.retain_artifacts(result, directory)
        return result

    def retain_artifacts(self, receipt, directory):
        total_bytes = 0
        for name in ("image", "audio", "video", "thumbnail"):
            artifact = receipt.get("assets", {}).get(name, receipt.get(name))
            if not isinstance(artifact, dict) or not isinstance(
                artifact.get("path"), str
            ):
                continue
            path = Path(artifact["path"])
            if not path.is_absolute():
                continue
            source = input_file(str(path))
            total_bytes += source.stat().st_size
            if total_bytes > MAXIMUM_ARTIFACT_BYTES:
                raise CapabilityError("artifact_too_large")
            target = directory / (name + source.suffix)
            shutil.copyfile(source, target)
            if (
                artifact.get("sha256") is not None
                and file_digest(target) != artifact["sha256"]
            ):
                raise CapabilityError("artifact_changed")
            artifact["gateway_path"] = str(target)
