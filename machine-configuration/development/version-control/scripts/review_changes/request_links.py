import os
import re
from dataclasses import dataclass
from pathlib import Path

from review_command_runner import ReviewTargetError, run_command

URL_CHARACTER = r"[^\s()<>\[\]\"'`]"
REQUEST_LINK_PATTERN = re.compile(
    rf"https?://(?P<host>{URL_CHARACTER}+?)/(?P<project_path>{URL_CHARACTER}+?)"
    r"(?:/-)?/(?:merge_requests|pull)/(?P<number>\d+)"
)
ORIGIN_PATTERN = re.compile(
    r"^(?:[a-z+]+://)?(?:[^@/]+@)?(?P<host>[^/:]+)(?::\d+)?[:/](?P<project_path>.+?)(?:\.git)?/?$"
)
LOCAL_CLONE_ROOTS = (Path.home() / "repo", Path.home())


@dataclass(frozen=True)
class ForgeRepository:
    host: str
    project_path: str

    @property
    def is_github(self) -> bool:
        return "github.com" in self.host


@dataclass(frozen=True)
class RequestLink:
    repository: ForgeRepository
    number: str

    @property
    def short_reference(self) -> str:
        number_sigil = "#" if self.repository.is_github else "!"
        return f"{number_sigil}{self.number}"

    @property
    def reference(self) -> str:
        return f"{self.repository.project_path}{self.short_reference}"


def request_link_from_match(link_match: re.Match) -> RequestLink:
    return RequestLink(
        ForgeRepository(link_match["host"], link_match["project_path"]),
        link_match["number"],
    )


def parse_request_link(raw_target: str) -> RequestLink | None:
    link_match = REQUEST_LINK_PATTERN.match(raw_target.strip())
    return request_link_from_match(link_match) if link_match else None


def find_request_links(text: str) -> list[RequestLink]:
    request_links = [
        request_link_from_match(link_match)
        for link_match in REQUEST_LINK_PATTERN.finditer(text)
    ]
    return list(dict.fromkeys(request_links))


def origin_repository(repository_directory: Path) -> ForgeRepository | None:
    result = run_command(
        ["git", "-C", str(repository_directory), "remote", "get-url", "origin"]
    )
    if result.returncode != 0:
        return None
    origin_match = ORIGIN_PATTERN.match(result.stdout.strip())
    if not origin_match:
        return None
    return ForgeRepository(origin_match["host"], origin_match["project_path"])


def is_clone_of(directory: Path, wanted_project_path: str) -> bool:
    repository = origin_repository(directory)
    return (
        repository is not None
        and repository.project_path.lower() == wanted_project_path.lower()
    )


def candidate_clone_directories(project_path: str) -> list[Path]:
    project_name = project_path.rsplit("/", 1)[-1]
    named_candidates = [root / project_name for root in LOCAL_CLONE_ROOTS]
    scanned_candidates = sorted(
        child for child in LOCAL_CLONE_ROOTS[0].glob("*") if child.is_dir()
    )
    return [*named_candidates, *scanned_candidates]


def find_local_clone(project_path: str) -> Path:
    if is_clone_of(Path.cwd(), project_path):
        return Path.cwd()
    for candidate_directory in candidate_clone_directories(project_path):
        if (candidate_directory / ".git").exists() and is_clone_of(
            candidate_directory, project_path
        ):
            return candidate_directory
    searched_roots = " or ".join(str(root) for root in LOCAL_CLONE_ROOTS)
    raise ReviewTargetError(f"no local clone of {project_path} in {searched_roots}")


def enter_local_clone(repository: ForgeRepository) -> None:
    os.chdir(find_local_clone(repository.project_path))
