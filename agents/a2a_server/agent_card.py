import dataclasses
import json


@dataclasses.dataclass(frozen=True)
class AgentCapability:
    id: str
    name: str
    description: str


@dataclasses.dataclass(frozen=True)
class AgentCard:
    name: str
    description: str
    endpoint_url: str
    version: str
    capabilities: tuple[AgentCapability, ...]

    def to_json_serializable_dict(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "url": self.endpoint_url,
            "version": self.version,
            "capabilities": [
                dataclasses.asdict(capability) for capability in self.capabilities
            ],
            "defaultInputModes": ["text"],
            "defaultOutputModes": ["text"],
        }

    def serialize_to_json_bytes(self) -> bytes:
        return json.dumps(self.to_json_serializable_dict(), indent=2).encode("utf-8")


def build_agent_card_from_environment(
    agent_name: str,
    description: str,
    endpoint_url: str,
    version: str = "0.1.0",
    capability_specifications: tuple[tuple[str, str, str], ...] = (),
) -> AgentCard:
    return AgentCard(
        name=agent_name,
        description=description,
        endpoint_url=endpoint_url,
        version=version,
        capabilities=tuple(
            AgentCapability(
                id=capability_id,
                name=capability_name,
                description=capability_description,
            )
            for capability_id, capability_name, capability_description in capability_specifications
        ),
    )
