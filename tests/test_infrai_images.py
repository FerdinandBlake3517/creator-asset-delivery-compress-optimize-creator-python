import base64
import json

import httpx

from creator_delivery.infrai_images import InfraiImages


def test_upload_sends_json_contract_fields() -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(
            200,
            json={"ok": True, "data": {"id": "img-1"}, "error": None, "metadata": {}},
        )

    client = InfraiImages("test-key", transport=httpx.MockTransport(handler))
    try:
        client.upload(b"image bytes", "cover.png", "asset-1")
    finally:
        client.close()

    request = requests[0]
    assert request.headers["Content-Type"] == "application/json"
    assert json.loads(request.content) == {
        "file": base64.b64encode(b"image bytes").decode("ascii"),
        "filename": "cover.png",
        "idempotency_key": "asset-upload:asset-1",
    }


def test_rate_limit_honors_retry_after_and_reuses_idempotency_key() -> None:
    requests: list[httpx.Request] = []
    sleeps: list[float] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        if len(requests) == 1:
            return httpx.Response(
                429,
                headers={"Retry-After": "2"},
                content=json.dumps({"ok": False, "data": None, "error": {"code": "REQUEST_REJECTED"}, "metadata": {}}),
            )
        return httpx.Response(
            200,
            content=json.dumps({"ok": True, "data": {"url": "https://cdn.example.test/a.webp"}, "error": None, "metadata": {}}),
        )

    client = InfraiImages(
        "test-key",
        transport=httpx.MockTransport(handler),
        sleep=sleeps.append,
    )
    try:
        result = client.compress("img-1", "asset-1", 4)
    finally:
        client.close()

    assert result["url"].endswith("a.webp")
    assert sleeps == [2.0]
    assert [request.headers["Content-Type"] for request in requests] == [
        "application/json",
        "application/json",
    ]
    assert [json.loads(request.content)["idempotency_key"] for request in requests] == [
        "asset-compress:asset-1:4",
        "asset-compress:asset-1:4",
    ]
    assert all(json.loads(request.content)["image"] == "img-1" for request in requests)
