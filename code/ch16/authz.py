"""Authorization guards: object-level (BOLA defense) and property-level
(BOPLA defense) checks, independent of any web framework.

Rule of thumb: authentication answers "who are you"; these guards answer
"may you touch *this* object" and "may you see/write *these* fields".
Records are plain mappings, so the guards work with ORM rows, dict stores,
or deserialized payloads alike.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Iterable, Mapping


class ForbiddenError(PermissionError):
    """Raised when a principal may not act on a resource."""


def _owner(resource: Mapping[str, Any]) -> str:
    try:
        return str(resource["owner_id"])
    except KeyError as exc:
        raise ForbiddenError("resource has no ownership metadata") from exc


def _tenant(resource: Mapping[str, Any]) -> str:
    try:
        return str(resource["tenant_id"])
    except KeyError as exc:
        raise ForbiddenError("resource has no tenant metadata") from exc


@dataclass(frozen=True)
class Guard:
    """Object-level authorization: every access names its subject."""

    actor_id: str
    tenant_id: str
    roles: frozenset[str] = field(default_factory=frozenset)

    def can_read(self, resource: Mapping[str, Any]) -> bool:
        if "admin" in self.roles:
            return _tenant(resource) == self.tenant_id
        return (
            _tenant(resource) == self.tenant_id
            and _owner(resource) == self.actor_id
        )

    def can_write(self, resource: Mapping[str, Any]) -> bool:
        # Writes are owner-only; even admins must use the audited admin API.
        return (
            _tenant(resource) == self.tenant_id
            and _owner(resource) == self.actor_id
        )

    def require_read(self, resource: Mapping[str, Any]) -> None:
        if not self.can_read(resource):
            raise ForbiddenError("read denied: not your object")

    def require_write(self, resource: Mapping[str, Any]) -> None:
        if not self.can_write(resource):
            raise ForbiddenError("write denied: not your object")


# Property-level policy: role -> fields the role may see or change.
# Absent roles get nothing; server-owned fields appear in NO write policy.
FieldPolicy = Mapping[str, frozenset[str]]

ROBOT_READ_POLICY: FieldPolicy = {
    "owner": frozenset(
        {"id", "name", "model", "status", "battery_pct", "last_seen", "notes"}
    ),
    "technician": frozenset({"id", "name", "model", "status", "battery_pct"}),
    "auditor": frozenset({"id", "name", "status", "firmware_version"}),
    "admin": frozenset(
        {
            "id", "name", "model", "status", "battery_pct", "last_seen",
            "notes", "firmware_version", "service_key_last4",
        }
    ),
}

ROBOT_WRITE_POLICY: FieldPolicy = {
    "owner": frozenset({"name", "notes"}),
    "technician": frozenset({"status", "notes"}),
    "admin": frozenset({"name", "status", "notes", "firmware_version"}),
}

_ROLE_PRECEDENCE = ("admin", "technician", "auditor", "owner")


def role_for(roles: Iterable[str]) -> str | None:
    """Pick the most privileged policy role the actor holds."""
    held = set(roles)
    for candidate in _ROLE_PRECEDENCE:
        if candidate in held:
            return candidate
    return None


def filter_fields(
    record: Mapping[str, Any], policy: FieldPolicy, roles: Iterable[str]
) -> dict[str, Any]:
    """Return only the fields the actor's role may read (BOPLA defense)."""
    role = role_for(roles)
    allowed = policy.get(role, frozenset()) if role else frozenset()
    return {key: value for key, value in record.items() if key in allowed}


def apply_patch(
    record: Mapping[str, Any],
    patch: Mapping[str, Any],
    policy: FieldPolicy,
    roles: Iterable[str],
) -> dict[str, Any]:
    """Apply only writable fields; reject anything else.

    Mass-assignment defense: the allow-list is the contract. Server-owned
    invariants (``id``, ``owner_id``, ``tenant_id``) are re-asserted from the
    stored record, never from the client patch.
    """
    role = role_for(roles)
    allowed = policy.get(role, frozenset()) if role else frozenset()
    rejected = sorted(set(patch) - allowed)
    if rejected:
        raise ForbiddenError(f"fields not writable by this role: {rejected}")
    updated = dict(record)
    for key in allowed & set(patch):
        updated[key] = patch[key]
    for invariant in ("id", "owner_id", "tenant_id"):
        updated[invariant] = record[invariant]
    return updated


def require_readable_factory(
    get_actor: Callable[[], Guard],
) -> Callable[[Mapping[str, Any]], Mapping[str, Any]]:
    """Adapt the guard to DI: fetch-then-authorize in one step."""

    def require_readable(resource: Mapping[str, Any]) -> Mapping[str, Any]:
        get_actor().require_read(resource)
        return resource

    return require_readable
