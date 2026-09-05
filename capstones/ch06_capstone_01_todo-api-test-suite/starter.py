"""Capstone 6.1 [junior] — Todo API with a Full Test Suite.

A minimal but complete FastAPI todo service. See README.md for the contract.
"""

from __future__ import annotations

import argparse
from typing import Protocol, Sequence

from pydantic import BaseModel, Field


class TodoCreate(BaseModel):
    """TODO: constrain title to 3-80 chars and priority to 1..5."""

    title: str = Field(min_length=3, max_length=80)
    priority: int = Field(ge=1, le=5)


class TodoRead(BaseModel):
    """Response model — no internal fields may leak into this shape."""

    id: int
    title: str
    priority: int
    completed: bool


class TodoRepository(Protocol):
    """Repository seam. TODO: the in-memory implementation must mint
    deterministic IDs per fresh app (no uuid/time/random)."""

    def add(self, data: TodoCreate) -> TodoRead: ...
    def get(self, todo_id: int) -> TodoRead | None: ...
    def list(self) -> list[TodoRead]: ...
    def complete(self, todo_id: int) -> TodoRead | None: ...
    def delete(self, todo_id: int) -> bool: ...


class InMemoryTodoRepository:
    """TODO: implement TodoRepository with deterministic sequential IDs."""

    def __init__(self, seed_todos: list[TodoCreate] | None = None) -> None:
        raise NotImplementedError("TODO: implement InMemoryTodoRepository")


def seed_fixture() -> list[TodoCreate]:
    """Return the 20 synthetic Northwind maintenance-log todos (seeded)."""
    raise NotImplementedError("TODO: build the deterministic 20-todo fixture")


def create_app(repository: TodoRepository | None = None) -> "object":
    """Build the FastAPI app.

    TODO: routes for create (201), read (404 when missing), list, complete,
    delete (204) — every route declares response_model; body-accepting
    routes document 422 in the OpenAPI schema.
    """
    raise NotImplementedError("TODO: implement create_app")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="todo-api", description=__doc__)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--dry-run", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.dry_run:
        print("DRY RUN: would create the todo app and serve it with uvicorn.")
        return 0
    print("Scaffold ready. Implement create_app in starter.py to begin.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
