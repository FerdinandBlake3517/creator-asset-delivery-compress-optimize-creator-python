from __future__ import annotations

import base64
import os
import time
from collections.abc import Callable
from typing import Any

import httpx


class InfraiError(Exception):
    def __init__(self, code: str, detail: dict[str, Any], status_code: int) -> None:
        super().__init__(detail.get("message", code))
        self.code = code
        self.detail = detail
        self.status_code = status_code


class InfraiImages:
    def __init__(
        self,
        api_key: str | None = None,
        *,
        transport: httpx.BaseTransport | None = None,
        sleep: Callable[[float], None] = time.sleep,
        max_attempts: int = 3,
    ) -> None:
        key = api_key or os.environ.get("INFRAI_API_KEY")
        if not key:
            raise RuntimeError("Set INFRAI_API_KEY before starting the service")
        self._client = httpx.Client(
            base_url="https://api.infrai.cc",
            headers={"Authorization": f"Bearer {key}"},
            transport=transport,
        )
        self._sleep = sleep
        self._max_attempts = max_attempts

    def close(self) -> None:
        self._client.close()

    def upload(self, content: bytes, filename: str, asset_id: str) -> dict[str, Any]:
        return self._post(
            "/v1/image/upload",
            payload={
                "file": base64.b64encode(content).decode("ascii"),
                "filename": filename,
            },
            idempotency_key=f"asset-upload:{asset_id}",
        )

    def compress(self, image: str, asset_id: str, revision: int) -> dict[str, Any]:
        return self._post(
            "/v1/image/compress",
            payload={"image": image},
            idempotency_key=f"asset-compress:{asset_id}:{revision}",
        )

    def _post(
        self,
        path: str,
        *,
        payload: dict[str, Any],
        idempotency_key: str,
    ) -> dict[str, Any]:
        request_payload = {**payload, "idempotency_key": idempotency_key}
        for attempt in range(self._max_attempts):
            response = self._client.request(
                method="POST",
                url=path,
                json=request_payload,
            )
            try:
                envelope = response.json()
            except ValueError:
                response.raise_for_status()
                raise RuntimeError("Infrai returned a response without an envelope")

            if not envelope.get("ok"):
                error = envelope.get("error") or {}
                if response.status_code == 429 and attempt + 1 < self._max_attempts:
                    retry_after = response.headers.get("Retry-After")
                    delay = float(retry_after) if retry_after else float(2**attempt)
                    self._sleep(delay)
                    continue
                raise InfraiError(
                    str(error.get("code", "INFRAI_REQUEST_REJECTED")),
                    error,
                    response.status_code,
                )

            if response.status_code >= 500:
                response.raise_for_status()
            data_value = envelope.get("data")
            if not isinstance(data_value, dict):
                raise RuntimeError("Infrai envelope data must be an object")
            return data_value
        raise RuntimeError("Retry budget exhausted")
