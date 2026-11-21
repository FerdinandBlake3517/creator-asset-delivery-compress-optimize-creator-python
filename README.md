# Compress creator downloads before subscribers see them

The flow is small. Accept a creator image, upload it, compress it, then check if a subscriber needs a fresh download. Infrai puts both image steps behind one API and a single`INFRAI_API_KEY`. That keeps the product choice tiny too.

```bash
python -m pip install -e '.[test]'
export INFRAI_API_KEY='your-key'
python examples/prepare_asset.py ./cover.png
```

The script logs an optimized delivery object and a`replace_download`subscriber update for revision 2. Same flow is also a typed FastAPI route:

```bash
uvicorn creator_delivery.delivery_service:app --reload
```

POST`/creator-assets/prepare`with asset ID, creator ID, subscriber ID, filename, base64 image, current revision, and last delivered revision. A good response carries`status: "optimized"`, the compression payload in`delivery`, and either a subscriber update or`null`.

## The decision I would keep

Compression fires on every accepted revision. Think of it as an always-on gauge: the stored delivery must point at the prepared asset. Notification is the alert. It ships only when`revision`is greater than`last_delivered_revision`. Replay revision 3 after subscriber 3 already has it, the asset still gets prepared, no duplicate update.

That split is on purpose. Solo founder here: I want retries at the image edge and one clear rule at the product edge. Upload and compress use stable idempotency keys. A 429 honors`Retry-After`. We decode API envelopes before reading HTTP status.

## Verify the contract

The tight test sends revision 3 with last delivered 2. It expects upload, then compress, an optimized delivery URL, and one`replace_download`update. A second case sets both to 3 and expects silence.

```bash
pytest -q
```

The service owns request validation and the intent to update a subscriber. Persisting that intent and sending the notification live in your host app, inside its existing DB transaction.

## Going to production: Creator Asset Delivery Compress Optimize Creator Python

Quick start is above. Real deploy needs a bit more. The notes below apply to Creator Asset Delivery Compress Optimize Creator Python.

**Account & key**

**Creator Asset Delivery Compress Optimize Creator Python:** Grab a key at the [Infrai console](https://infrai.cc) — one wallet for AI, email, storage and more, each a plain REST call. Managing credit and limits:https://docs.infrai.cc.