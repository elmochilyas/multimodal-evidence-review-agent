"""Image loading and base64 encoding utilities for vision model calls."""

import base64
import mimetypes
from pathlib import Path
from typing import List, Tuple

from src.io_utils import split_image_paths


def guess_mime_type(image_path: str) -> str:
    """Guess the MIME type for an image path, defaulting to image/jpeg."""
    mime, _ = mimetypes.guess_type(image_path)
    if mime and mime.startswith("image/"):
        return mime
    return "image/jpeg"


def encode_image_to_data_url(image_path: str) -> Tuple[str, bool]:
    """Encode a local image file to a base64 data URL.

    Returns (data_url, success). On failure, data_url is an error message.
    """
    path = Path(image_path)
    if not path.exists():
        return (f"Image not found: {image_path}", False)
    if not path.is_file():
        return (f"Not a file: {image_path}", False)

    try:
        data = path.read_bytes()
        if not data:
            return (f"Empty image file: {image_path}", False)
        mime = guess_mime_type(image_path)
        b64 = base64.b64encode(data).decode("utf-8")
        return (f"data:{mime};base64,{b64}", True)
    except Exception as exc:  # pragma: no cover - defensive
        return (f"Failed to read image {image_path}: {exc}", False)


def load_images_for_model(
    image_paths: str, base_dir: str = "."
) -> Tuple[List[str], List[str]]:
    """Load all images referenced by semicolon-separated paths.

    Returns (data_urls, errors). Missing or unreadable images are reported in
    errors and omitted from data_urls.
    """
    data_urls: List[str] = []
    errors: List[str] = []

    for raw_path in split_image_paths(image_paths):
        path = Path(raw_path)
        if not path.is_absolute():
            path = Path(base_dir) / path

        data_url, ok = encode_image_to_data_url(str(path))
        if ok:
            data_urls.append(data_url)
        else:
            errors.append(data_url)

    return data_urls, errors
