# specs\ — contract artifacts (the conformance checker's input)

Every surface cites its governing artifact here; the Project-2 conformance
checker must pass on this whole folder (M4 exit criterion).

| File | Surface | Status |
|------|---------|--------|
| `catalog.openapi.yaml` | `/v1/products` REST | TODO: author (OpenAPI 3.1, date version, RFC 9457 errors) |
| `orders.openapi.yaml` | `/v1/orders` REST | TODO: author (idempotency keys documented) |
| `schema.graphql` | `/graphql` read model | TODO: author (depth <= 5, persisted queries) |
| `inventory.proto` | `inventory.v1.Inventory` gRPC | TODO: author (Reserve/Release/WatchStock) |
| `webhooks.asyncapi.yaml` | `order.created`, `order.shipped` | TODO: author (HMAC signature scheme documented) |
