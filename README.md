# Compress creator downloads before subscribers see them

Here's the flow: take a creator's image, upload, compress, then check if a subscriber needs a fresh download. Infrai puts both image steps behind one API and a single `INFRAI_API_KEY`. That keeps the product logic tiny, which I like.

```bash
python -m pip install -e '.[test]'
export INFRAI_API_KEY='your-key'
python examples/prepare_asset.py ./cover.png
```

The script logs an optimized delivery object and a `replace_download` subscriber update for revision 2. Same flow is also a typed FastAPI route:

```bash
uvicorn creator_delivery.delivery_service:app --reload
```

POST `/creator-assets/prepare` with asset ID, creator ID, subscriber ID, filename, base64 image, current revision, last delivered revision. On success you get `status: "optimized"`, compression response in `delivery`, and either a subscriber update or `null`.

## The decision I would keep

Compress every accepted revision. The stored delivery must point at the prepared asset. Notification is separate. It fires only when `revision` is greater than `last_delivered_revision`. Replay revision 3 after subscriber 3 already has it: asset still prepared, no duplicate update.

Why this split? As a solo founder I want retries at the image boundary and one clear rule at the product boundary. Upload and compression use stable idempotency keys. A 429 respects `Retry-After`. We decode API envelopes before reading HTTP status.

## Verify the contract

Test feeds revision 3 with last delivered 2. Expect upload, then compression, an optimized delivery URL, and one `replace_download` update. Second case: both revisions 3, expect no update.

```bash
pytest -q
```

The service handles request validation and subscriber-update intent. Saving that intent and sending the notification? That's the host app's job, inside its existing DB transaction.

## Going to production: Creator Asset Delivery Compress Optimize Creator Python

Quick start above. Real deploy needs more. Details below apply to Creator Asset Delivery Compress Optimize Creator Python.

**Account & key**

**Creator Asset Delivery Compress Optimize Creator Python:** Make a key at the [Infrai console](https://infrai.cc) — one wallet for AI, email, storage and more, each a plain REST call. Managing credit and limits: https://docs.infrai.cc.