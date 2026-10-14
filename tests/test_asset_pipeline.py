import base64

from creator_delivery.asset_pipeline import CreatorAssetRequest, prepare_creator_asset


class RecordingImages:
    def __init__(self) -> None:
        self.calls: list[tuple[object, ...]] = []

    def upload(self, content: bytes, filename: str, asset_id: str) -> dict[str, str]:
        self.calls.append(("upload", content, filename, asset_id))
        return {"id": "img_creator_42"}

    def compress(self, image: str, asset_id: str, revision: int) -> dict[str, str]:
        self.calls.append(("compress", image, asset_id, revision))
        return {"url": "https://cdn.example.test/optimized/poster.webp"}


def make_request(revision: int, last_delivered_revision: int) -> CreatorAssetRequest:
    return CreatorAssetRequest(
        asset_id="poster-42",
        creator_id="creator-7",
        subscriber_id="subscriber-9",
        filename="launch-poster.png",
        image_base64=base64.b64encode(b"image bytes").decode("ascii"),
        revision=revision,
        last_delivered_revision=last_delivered_revision,
    )


def test_new_revision_is_compressed_and_marks_subscriber_download_for_replacement() -> None:
    images = RecordingImages()

    result = prepare_creator_asset(make_request(3, 2), images)

    assert result.status == "optimized"
    assert result.delivery["url"].endswith("poster.webp")
    assert result.subscriber_update is not None
    assert result.subscriber_update.action == "replace_download"
    assert images.calls == [
        ("upload", b"image bytes", "launch-poster.png", "poster-42"),
        ("compress", "img_creator_42", "poster-42", 3),
    ]


def test_already_delivered_revision_does_not_repeat_subscriber_update() -> None:
    result = prepare_creator_asset(make_request(3, 3), RecordingImages())

    assert result.status == "optimized"
    assert result.subscriber_update is None

