from __future__ import annotations

from fastapi import FastAPI, HTTPException

from .asset_pipeline import CreatorAssetRequest, PreparedAsset, prepare_creator_asset
from .infrai_images import InfraiError, InfraiImages

app = FastAPI(title="Creator asset delivery")


@app.post("/creator-assets/prepare", response_model=PreparedAsset)
def prepare(request: CreatorAssetRequest) -> PreparedAsset:
    images = InfraiImages()
    try:
        return prepare_creator_asset(request, images)
    except InfraiError as exc:
        status = exc.status_code if 400 <= exc.status_code < 500 else 502
        raise HTTPException(
            status_code=status,
            detail={"code": exc.code, "message": str(exc)},
        ) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    finally:
        images.close()

