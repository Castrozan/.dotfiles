import asyncio
import os
import sys
from pathlib import Path

from app_server import CodexConfigurationClient
from launch_arguments import HookDiscoveryRequest, discover_launch_request


approval_timeout_seconds = 8
session_page_size = 100
hook_directory_batch_size = 25


async def session_directories(client: CodexConfigurationClient) -> set[Path]:
    directories = set()
    cursor = None
    while True:
        response = await client.request(
            "thread/list",
            {
                "cursor": cursor,
                "limit": session_page_size,
                "modelProviders": [],
                "useStateDbOnly": True,
            },
        )
        directories.update(
            Path(thread["cwd"])
            for thread in response["data"]
            if Path(thread["cwd"]).is_dir()
        )
        cursor = response.get("nextCursor")
        if cursor is None:
            return directories


async def approve_discovered_hooks(
    client: CodexConfigurationClient, directories: list[Path]
) -> None:
    trust_updates = {}
    for offset in range(0, len(directories), hook_directory_batch_size):
        response = await client.request(
            "hooks/list",
            {
                "cwds": [
                    str(directory)
                    for directory in directories[
                        offset : offset + hook_directory_batch_size
                    ]
                ]
            },
        )
        for entry in response["data"]:
            for hook in entry["hooks"]:
                if hook["trustStatus"] in {"untrusted", "modified"}:
                    trust_updates[hook["key"]] = {"trusted_hash": hook["currentHash"]}
    if trust_updates:
        await client.request(
            "config/batchWrite",
            {
                "edits": [
                    {
                        "keyPath": "hooks.state",
                        "value": trust_updates,
                        "mergeStrategy": "upsert",
                    }
                ],
                "reloadUserConfig": True,
            },
        )


async def approve_launch_hooks(binary: str, discovery: HookDiscoveryRequest) -> None:
    process = await asyncio.create_subprocess_exec(
        binary,
        *discovery.configuration_arguments,
        "app-server",
        cwd=discovery.working_directory,
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.DEVNULL,
        limit=4 * 1024 * 1024,
    )
    try:
        async with asyncio.timeout(approval_timeout_seconds):
            client = CodexConfigurationClient(process)
            await client.initialize()
            directories = {discovery.working_directory}
            if discovery.include_session_directories:
                directories.update(await session_directories(client))
            await approve_discovered_hooks(client, sorted(directories))
    finally:
        if process.returncode is None:
            process.kill()
        await process.communicate()


def main() -> int:
    try:
        discovery = discover_launch_request(sys.argv[1:])
        if discovery is not None:
            asyncio.run(
                approve_launch_hooks(os.environ["CODEX_LAUNCHER_BINARY"], discovery)
            )
    except (OSError, ValueError, RuntimeError) as error:
        detail = str(error) or f"exceeded {approval_timeout_seconds} seconds"
        print(f"Codex hook approval failed: {detail}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
