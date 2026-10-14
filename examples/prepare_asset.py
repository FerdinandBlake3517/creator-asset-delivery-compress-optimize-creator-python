from __future__ import annotations

import base64
import sys
from pathlib import Path

from creator_delivery.asset_pipeline import CreatorAssetRequest, prepare_creator_asset
from creator_delivery.infrai_images import InfraiImages


def main() -> None:
    image_path = Path(sys.argv[1])
    request = CreatorAssetRequest(
        asset_id="creator-release-cover",
        creator_id="creator-demo",
        subscriber_id="subscriber-demo",
        filename=image_path.name,
        image_base64=base64.b64encode(image_path.read_bytes()).decode("ascii"),
        revision=2,
        last_delivered_revision=1,
    )
    images = InfraiImages()
    try:
        print(prepare_creator_asset(request, images).model_dump_json(indent=2))
    finally:
        images.close()


if __name__ == "__main__":
    main()

