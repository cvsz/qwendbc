from __future__ import annotations

from app.agentic.domain import AgentDefinition


class AgentNotFound(LookupError):
    pass


class AgentRegistry:
    def __init__(self, definitions: tuple[AgentDefinition, ...]) -> None:
        self._definitions = {definition.id: definition for definition in definitions}
        if len(self._definitions) != len(definitions):
            raise ValueError("Agent IDs must be unique")

    def list(self) -> tuple[AgentDefinition, ...]:
        return tuple(self._definitions[key] for key in sorted(self._definitions))

    def get(self, agent_id: str) -> AgentDefinition:
        try:
            return self._definitions[agent_id]
        except KeyError as exc:
            raise AgentNotFound(agent_id) from exc


def build_default_agent_registry() -> AgentRegistry:
    read_capabilities = ("workspace.read", "rag.search", "model.invoke")
    definitions = (
        AgentDefinition(
            id="supervisor",
            name="Supervisor",
            description="Decomposes bounded work and selects specialist agents.",
            capabilities=("agent.delegate", *read_capabilities),
            allowed_tools=(),
            approval_policy="deny_external_writes",
            max_runtime_seconds=300,
            max_steps=12,
        ),
        AgentDefinition(
            id="researcher",
            name="Researcher",
            description="Collects source-backed context without external writes.",
            capabilities=("connector.read", *read_capabilities),
            allowed_tools=(),
            approval_policy="read_only",
            max_runtime_seconds=300,
            max_steps=10,
        ),
        AgentDefinition(
            id="planner",
            name="Planner",
            description="Produces bounded execution plans without side effects.",
            capabilities=read_capabilities,
            allowed_tools=(),
            approval_policy="read_only",
            max_runtime_seconds=180,
            max_steps=8,
        ),
        AgentDefinition(
            id="coding_executor",
            name="Coding Executor",
            description="Reserved execution role; tool execution is not enabled yet.",
            capabilities=("workspace.read", "workspace.write"),
            allowed_tools=(),
            approval_policy="require_approval",
            max_runtime_seconds=600,
            max_steps=20,
        ),
        AgentDefinition(
            id="rag_specialist",
            name="RAG Specialist",
            description="Performs authorized local retrieval and ingestion planning.",
            capabilities=("rag.search", "rag.ingest"),
            allowed_tools=(),
            approval_policy="deny_external_writes",
            max_runtime_seconds=300,
            max_steps=10,
        ),
        AgentDefinition(
            id="security_reviewer",
            name="Security Reviewer",
            description="Reviews task evidence and trust-boundary changes.",
            capabilities=("workspace.read", "rag.search"),
            allowed_tools=(),
            approval_policy="read_only",
            max_runtime_seconds=300,
            max_steps=12,
        ),
        AgentDefinition(
            id="qa_verifier",
            name="QA Verifier",
            description="Verifies evidence and test outcomes without granting approval.",
            capabilities=("workspace.read",),
            allowed_tools=(),
            approval_policy="read_only",
            max_runtime_seconds=300,
            max_steps=12,
        ),
        AgentDefinition(
            id="documentation",
            name="Documentation Agent",
            description="Produces documentation from verified implementation evidence.",
            capabilities=("workspace.read",),
            allowed_tools=(),
            approval_policy="read_only",
            max_runtime_seconds=300,
            max_steps=10,
        ),
    )
    return AgentRegistry(definitions)
