"""Tests for the authorization guards in authz.py."""

from __future__ import annotations

import pytest

from authz import (
    ROBOT_READ_POLICY,
    ROBOT_WRITE_POLICY,
    ForbiddenError,
    Guard,
    apply_patch,
    filter_fields,
)

ALICE_ROBOT = {
    "id": 1001,
    "name": "Welder-7",
    "model": "NR-220",
    "status": "idle",
    "battery_pct": 88,
    "last_seen": "2026-08-30T09:14:00Z",
    "notes": "dock 3",
    "owner_id": "alice",
    "tenant_id": "tenant-nwr",
    "firmware_version": "4.2.0",
    "service_key": "sk_test_DEMO_robot1001_invalid",
    "service_key_last4": "1001",
    "maintenance_mode": False,
}

OWNER = Guard(actor_id="alice", tenant_id="tenant-nwr", roles=frozenset({"owner"}))
STRANGER = Guard(actor_id="mallory", tenant_id="tenant-nwr", roles=frozenset({"owner"}))
ADMIN = Guard(actor_id="carol", tenant_id="tenant-nwr", roles=frozenset({"admin"}))
CROSS_TENANT = Guard(actor_id="alice", tenant_id="tenant-other", roles=frozenset({"admin"}))


def test_owner_reads_own_robot() -> None:
    OWNER.require_read(ALICE_ROBOT)


def test_stranger_denied_read_and_write() -> None:
    with pytest.raises(ForbiddenError):
        STRANGER.require_read(ALICE_ROBOT)
    with pytest.raises(ForbiddenError):
        STRANGER.require_write(ALICE_ROBOT)


def test_admin_reads_but_does_not_own_write() -> None:
    ADMIN.require_read(ALICE_ROBOT)
    with pytest.raises(ForbiddenError):
        ADMIN.require_write(ALICE_ROBOT)


def test_cross_tenant_admin_denied() -> None:
    with pytest.raises(ForbiddenError):
        CROSS_TENANT.require_read(ALICE_ROBOT)


def test_filter_fields_hides_secrets_from_owner() -> None:
    view = filter_fields(ALICE_ROBOT, ROBOT_READ_POLICY, ["owner"])
    assert "service_key" not in view
    assert "owner_id" not in view
    assert view["name"] == "Welder-7"


def test_filter_fields_admin_gets_last4_not_secret() -> None:
    view = filter_fields(ALICE_ROBOT, ROBOT_READ_POLICY, ["admin"])
    assert view["service_key_last4"] == "1001"
    assert "service_key" not in view


def test_filter_fields_unknown_role_gets_nothing() -> None:
    assert filter_fields(ALICE_ROBOT, ROBOT_READ_POLICY, ["intruder"]) == {}


def test_apply_patch_allows_writable_fields() -> None:
    updated = apply_patch(
        ALICE_ROBOT, {"name": "Welder-7b"}, ROBOT_WRITE_POLICY, ["owner"]
    )
    assert updated["name"] == "Welder-7b"
    assert updated["owner_id"] == "alice"


def test_apply_patch_rejects_server_owned_fields() -> None:
    with pytest.raises(ForbiddenError):
        apply_patch(
            ALICE_ROBOT,
            {"owner_id": "mallory"},
            ROBOT_WRITE_POLICY,
            ["owner"],
        )


def test_apply_patch_reinstates_invariants_even_for_admin() -> None:
    forged = dict(ALICE_ROBOT)
    forged["owner_id"] = "mallory"
    updated = apply_patch(
        forged, {"status": "charging"}, ROBOT_WRITE_POLICY, ["admin"]
    )
    assert updated["owner_id"] == "mallory"  # stored value preserved verbatim
    assert updated["status"] == "charging"
