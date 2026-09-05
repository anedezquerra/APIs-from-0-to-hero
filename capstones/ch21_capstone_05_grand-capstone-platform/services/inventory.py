"""Inventory service (M2): inventory.v1.Inventory gRPC surface.

TODO: Reserve / Release / WatchStock (server stream); an in-process stub
implementation is acceptable offline — keep the interface protobuf-shaped
(specs\inventory.proto is the contract).
Backed by ..\..\..\datasets\northwind_robotics\inventory.csv.
"""

from __future__ import annotations


class InventoryService:
    """TODO: implement Reserve/Release/WatchStock per specs/inventory.proto."""

    def reserve(self, sku: str, quantity: int) -> bool:
        raise NotImplementedError("TODO: implement reserve")

    def release(self, sku: str, quantity: int) -> None:
        raise NotImplementedError("TODO: implement release")

    def watch_stock(self, sku: str) -> "object":
        """Server-streaming stock updates."""
        raise NotImplementedError("TODO: implement watch_stock")
