# Webhook fixtures (chapter 11)

Synthetic signed-webhook payloads implementing the book's chapter 11 scheme:

* Signature: `HMAC-SHA256(key, "<timestamp>.<body>")`, hex-encoded.
* Header: `X-Northwind-Signature: t=<unix_ts>,v1=<hex>`.
* Receivers must reject timestamps older than 5 minutes (replay protection).

## Files

| File | Event | Expected verification |
|---|---|---|
| `orders_created.json` | `orders.created` | pass |
| `orders_fulfilled.json` | `orders.fulfilled` | pass |
| `inventory_low_stock.json` | `inventory.low_stock` | pass |
| `bad_signature.json` | `orders.created` (tampered) | **fail** |
| `TEST-ONLY_signing_key.txt` | shared test key | n/a |

Each fixture is JSON with `headers` and the exact raw `body` string. Verify with:

```powershell
# PowerShell-friendly Python one-liner style; see chapter 11 labs for full code
python -c "import hmac,hashlib,json; f=json.load(open(r'datasets\northwind_robotics\webhooks\orders_created.json')); k=open(r'datasets\northwind_robotics\webhooks\TEST-ONLY_signing_key.txt').read().split('key: ')[1].strip().encode(); t=f['timestamp']; sig=hmac.new(k, f'{t}.{f["body"]}'.encode(), hashlib.sha256).hexdigest(); print('pass' if f't={t},v1={sig}' == f['headers']['X-Northwind-Signature'] else 'fail')"
```

All keys, IDs, and payloads are synthetic and safe to commit.
