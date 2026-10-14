from __future__ import annotations

import base64
import binascii
from collections.abc import Callable
from typing import Any, Protocol

from pydantic import BaseModel, Field, field_validator


class CreatorAssetRequest(BaseModel):
    asset_id: str = Field(min_length=1)
    creator_id: str = Field(min_length=1)
    subscriber_id: str = Field(min_length=1)
    filename: str = Field(min_length=1)
    image_base64: str = Field(min_length=1)
    revision: int = Field(ge=1)
    last_delivered_revision: int = Field(ge=0)

    @field_validator("filename")
    @classmethod
    def image_filename(cls, value: str) -> str:
        if not value.lower().endswith((".jpg", ".jpeg", ".png", ".webp")):
            raise ValueError("filename must use jpg, jpeg, png, or webp")
        return value


class SubscriberUpdate(BaseModel):
    subscriber_id: str
    asset_id: str
    revision: int
    action: str


class PreparedAsset(BaseModel):
    asset_id: str
    creator_id: str
    revision: int
    status: str
    delivery: dict[str, Any]
    subscriber_update: SubscriberUpdate | None


class ImageGateway(Protocol):
    upload: Callable[[bytes, str, str], dict[str, Any]]
    compress: Callable[[str, str, int], dict[str, Any]]


def prepare_creator_asset(request: CreatorAssetRequest, images: ImageGateway) -> PreparedAsset:
    try:
        content = base64.b64decode(request.image_base64, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise ValueError("image_base64 must contain valid base64") from exc

    uploaded = images.upload(content, request.filename, request.asset_id)
    image_reference = uploaded.get("id")
    if not isinstance(image_reference, str) or not image_reference:
        raise RuntimeError("Upload result must include an image id")

    delivery = images.compress(image_reference, request.asset_id, request.revision)
    subscriber_update = None
    if request.revision > request.last_delivered_revision:
        subscriber_update = SubscriberUpdate(
            subscriber_id=request.subscriber_id,
            asset_id=request.asset_id,
            revision=request.revision,
            action="replace_download",
        )

    return PreparedAsset(
        asset_id=request.asset_id,
        creator_id=request.creator_id,
        revision=request.revision,
        status="optimized",
        delivery=delivery,
        subscriber_update=subscriber_update,
    )
