"""Tests for image normalization and data URL encoding."""

import base64

from src.image_utils import encode_image_to_data_url, load_images_for_model


def _create_image_bytes(
    tmp_path, filename: str, mode: str = "RGB", ext: str = "png"
) -> str:
    """Create a small image file and return its path."""
    from PIL import Image

    path = tmp_path / filename
    if mode == "RGBA":
        img = Image.new("RGBA", (20, 20), (255, 0, 0, 128))
    elif mode == "P":
        img = Image.new("P", (20, 20))
    elif mode == "L":
        img = Image.new("L", (20, 20))
    else:
        img = Image.new("RGB", (20, 20), (255, 0, 0))
    img.save(path, format=ext.upper())
    return str(path)


def test_png_with_jpg_extension_is_encoded_as_jpeg(tmp_path) -> None:
    path = _create_image_bytes(tmp_path, "fake.jpg", mode="RGB", ext="png")
    data_url, ok = encode_image_to_data_url(path)
    assert ok
    assert data_url.startswith("data:image/jpeg;base64,")


def test_rgba_image_converted_to_rgb_jpeg(tmp_path) -> None:
    path = _create_image_bytes(tmp_path, "alpha.png", mode="RGBA", ext="png")
    data_url, ok = encode_image_to_data_url(path)
    assert ok
    assert data_url.startswith("data:image/jpeg;base64,")
    # Decode and verify it is valid JPEG data.
    b64 = data_url.split(",")[1]
    raw = base64.b64decode(b64)
    assert raw.startswith(b"\xff\xd8\xff")  # JPEG magic bytes


def test_invalid_image_file_handled_safely(tmp_path) -> None:
    path = tmp_path / "not_an_image.jpg"
    path.write_text("this is not image data", encoding="utf-8")
    data_url, ok = encode_image_to_data_url(str(path))
    assert not ok
    assert "Failed to normalize image" in data_url or "not found" in data_url


def test_missing_image_file_handled_safely(tmp_path) -> None:
    path = tmp_path / "missing.jpg"
    data_url, ok = encode_image_to_data_url(str(path))
    assert not ok
    assert "not found" in data_url.lower()


def test_load_images_for_model_omits_invalid_images(tmp_path) -> None:
    valid_path = _create_image_bytes(tmp_path, "valid.jpg", mode="RGB", ext="jpeg")
    invalid_path = tmp_path / "invalid.jpg"
    invalid_path.write_text("not an image", encoding="utf-8")

    image_paths = f"{valid_path};{invalid_path}"
    data_urls, errors = load_images_for_model(image_paths)

    assert len(data_urls) == 1
    assert len(errors) == 1
    assert data_urls[0].startswith("data:image/jpeg;base64,")
    assert "Failed to normalize image" in errors[0]


def test_no_raw_unsupported_bytes_sent_as_data_url(tmp_path) -> None:
    """Ensure the data URL payload is always normalized JPEG, never raw extension-guessed bytes."""
    path = tmp_path / "webp.jpg"
    from PIL import Image

    img = Image.new("RGB", (20, 20), (0, 255, 0))
    img.save(path, format="WEBP")

    data_url, ok = encode_image_to_data_url(str(path))
    assert ok
    assert data_url.startswith("data:image/jpeg;base64,")
    b64 = data_url.split(",")[1]
    raw = base64.b64decode(b64)
    assert raw.startswith(b"\xff\xd8\xff")
