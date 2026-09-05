"""Tests for the STRIDE worksheet generator."""

from __future__ import annotations

from stride_worksheet import generate_worksheet

SPEC = {
    "openapi": "3.0.3",
    "info": {"title": "NWR Fleet API", "version": "1.0.0"},
    "paths": {
        "/v1/robots/{robot_id}": {
            "get": {
                "summary": "Fetch one robot",
                "security": [{"bearer": ["fleet:read"]}],
                "parameters": [
                    {"name": "robot_id", "in": "path", "required": True}
                ],
                "responses": {"200": {"description": "ok"}},
            },
            "patch": {
                "summary": "Update a robot",
                "security": [{"bearer": ["fleet:write"]}],
                "parameters": [
                    {"name": "robot_id", "in": "path", "required": True}
                ],
                "responses": {"200": {"description": "ok"}, "429": {"description": "limited"}},
            },
        },
        "/v1/admin/users": {
            "get": {"summary": "List users", "responses": {"200": {"description": "ok"}}}
        },
    },
}


def test_endpoints_appear_sorted() -> None:
    out = generate_worksheet(SPEC)
    assert "## GET /v1/admin/users" in out
    assert out.index("## GET /v1/admin/users") < out.index("## GET /v1/robots/{robot_id}")


def test_bola_flag_on_path_id() -> None:
    out = generate_worksheet(SPEC)
    assert "object-level authorization (BOLA)" in out


def test_missing_security_flags_spoofing() -> None:
    out = generate_worksheet(SPEC)
    assert "no security scheme declared on operation" in out


def test_admin_path_flags_elevation() -> None:
    out = generate_worksheet(SPEC)
    assert "function-level role check required" in out


def test_write_method_flags_mass_assignment() -> None:
    out = generate_worksheet(SPEC)
    assert "mass assignment" in out


def test_missing_429_flags_dos() -> None:
    out = generate_worksheet(SPEC)
    # GET /v1/admin/users has no 429 documented
    assert "no 429 documented" in out


def test_documented_429_not_flagged_for_patch() -> None:
    out = generate_worksheet(SPEC)
    patch_block = out.split("## PATCH /v1/robots/{robot_id}")[1]
    assert "no 429 documented" not in patch_block.split("##")[0]
