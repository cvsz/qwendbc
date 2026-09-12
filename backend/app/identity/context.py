from __future__ import annotations

from dataclasses import dataclass
import hashlib
from typing import Literal

AuthenticationMethod = Literal["local", "bearer"]


@dataclass(frozen=True)
class PrincipalContext:
    """Verified request identity used by application authorization boundaries."""

    principal_id: str
    tenant_id: str
    subject: str
    roles: tuple[str, ...]
    scopes: frozenset[str]
    authentication_method: AuthenticationMethod

    def has_scope(self, scope: str) -> bool:
        return "*" in self.scopes or scope in self.scopes


def build_local_principal_context(
    authorization_header: str,
    *,
    bearer_verified: bool,
) -> PrincipalContext:
    """Build the backward-compatible single-owner identity context.

    The principal digest deliberately uses the same source material as the
    historical Cowork implementation so existing conversation/workspace data
    remains addressable across this refactor.
    """

    material = authorization_header if authorization_header else "local-access"
    principal_id = hashlib.sha256(material.encode("utf-8")).hexdigest()
    return PrincipalContext(
        principal_id=principal_id,
        tenant_id="local",
        subject="local-operator",
        roles=("owner",),
        scopes=frozenset({"*"}),
        authentication_method="bearer" if bearer_verified else "local",
    )
