from dataclasses import dataclass

from cycle_commands import CommandRunner
from cycle_configuration import UPSTREAM_BRANCH, CycleConfiguration
from cycle_repository import Repository


@dataclass(frozen=True)
class EntrypointObservation:
    head: str = ""
    settled: bool = True
    behind: int = 0
    ahead: int = 0
    commit_time: int = 0
    activation_reads_working_tree: bool = True

    def as_facts(self) -> dict:
        return {
            "entrypoint_head": self.head,
            "entrypoint_settled": self.settled,
            "entrypoint_behind": self.behind,
            "entrypoint_ahead": self.ahead,
            "activation_reads_working_tree": self.activation_reads_working_tree,
        }


def entrypoint_settled(entrypoint: Repository) -> bool:
    return (
        entrypoint.current_branch() == UPSTREAM_BRANCH
        and not entrypoint.operation_in_progress()
        and entrypoint.is_clean()
    )


def observe_entrypoint(
    configuration: CycleConfiguration, runner: CommandRunner
) -> EntrypointObservation:
    if configuration.entrypoint is None:
        return EntrypointObservation()
    entrypoint = Repository(configuration.entrypoint, runner)
    entrypoint.fetch()
    head = entrypoint.revision("HEAD")
    behind, ahead = entrypoint.divergence()
    return EntrypointObservation(
        head=head,
        settled=entrypoint_settled(entrypoint),
        behind=behind,
        ahead=ahead,
        commit_time=entrypoint.commit_time(head),
        activation_reads_working_tree=False,
    )
