"""Image loading and base64 encoding utilities for vision model calls."""

import base64
import io
from pathlib import Path
from typing import List, Tuple

from src.io_utils import split_image_paths


def _normalize_image_to_jpeg(image_path: str) -> Tuple[bytes, str]:
    """Open an image with Pillow, apply EXIF orientation, convert to RGB, and return JPEG bytes.

    Returns (jpeg_bytes, error_message). On success error_message is empty.
    """
    try:
        from PIL import Image, ImageOps
    except ImportError as exc:  # pragma: no cover - dependency issue
        return b"", f"Pillow is required for image normalization: {exc}"

    path = Path(image_path)
    if not path.exists():
        return b"", f"Image not found: {image_path}"
    if not path.is_file():
        return b"", f"Not a file: {image_path}"

    try:
        with Image.open(path) as img:
            # Apply EXIF orientation if available.
            img = ImageOps.exif_transpose(img)
            # Convert to RGB (handles RGBA, P, L, etc.).
            rgb = img.convert("RGB")
            buffer = io.BytesIO()
            rgb.save(buffer, format="JPEG", quality=95)
            return buffer.getvalue(), ""
    except Exception as exc:
        return b"", f"Failed to normalize image {image_path}: {exc}"


def encode_image_to_data_url(image_path: str) -> Tuple[str, bool]:
    """Encode a local image file to a normalized JPEG base64 data URL.

    Returns (data_url, success). On failure, data_url is an error message.
    """
    data, error = _normalize_image_to_jpeg(image_path)
    if error:
        return (error, False)
    if not data:
        return (f"Empty normalized image: {image_path}", False)

    b64 = base64.b64encode(data).decode("utf-8")
    return (f"data:image/jpeg;base64,{b64}", True)


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
