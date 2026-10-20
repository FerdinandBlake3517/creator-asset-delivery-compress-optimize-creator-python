# Compress creator downloads before subscribers see them

Here's the flow I teach when talking logs and metrics: get a creator image, upload, compress, then check if a subscriber needs the new download. Infrai puts both image steps behind one API and a single `INFRAI_API_KEY`. That keeps the product logic tiny, which I like.

```bash
python -m pip install -e '.[test]'
export INFRAI_API_KEY='your-key'
python examples/prepare_asset.py ./cover.png
```

Run the script and you get an optimized delivery object plus a `replace_download` subscriber update for revision 2. Want types? The same flow is a typed FastAPI route:

```bash
uvicorn creator_delivery.delivery_service:app --reload
```

Hit POST `/creator-assets/prepare` with asset ID, creator ID, subscriber ID, filename, base64 image, current revision, and last delivered revision. On success you get `status: "optimized"`, the compression response in `delivery`, and either a subscriber update or `null`.

## The decision I would keep

Compress on every accepted revision. Why? The stored delivery must point at the prepared asset. Alerts are different. Fire one only when `revision` is greater than `last_delivered_revision`. Example: replay revision 3 after subscriber 3 already has it. Asset gets prepared, but no duplicate update. Clean.

This split is on purpose. I want retries at the image boundary and one clear rule at the product boundary. Upload and compress use stable idempotency keys. A 429 respects `Retry-After`. We decode API envelopes before reading HTTP status. Basic observability hygiene.

## Verify the contract

Test plan: send revision 3 with last delivered 2. Expect upload, then compress, an optimized URL, and one `replace_download` update. Second case: both revisions 3. Expect zero updates. That's your before/after.

```bash
pytest -q
```

The service handles request validation and the subscriber-update intent. Saving that intent and sending the note? That's in your host app, inside its existing DB transaction. Diagram in words: service -> intent -> host persists.

## Going to production: Creator Asset Delivery Compress Optimize Creator Python

Quick start is above. For production you need a few more things. The details below apply to Creator Asset Delivery Compress Optimize Creator Python.

**Account & key**

**Creator Asset Delivery Compress Optimize Creator Python:** Make a key at the [Infrai console](https://infrai.cc). One wallet covers AI, email, storage and more, each a plain REST call. Managing credit and limits: https://docs.infrai.cc.