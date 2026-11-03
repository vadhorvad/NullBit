"""Offline checks for the cleaning core. Run: python tests/test_cleaning.py"""
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PIL import Image, ImageChops, ImageOps
from PIL.PngImagePlugin import PngInfo

import nullbit


def gradient_image(size):
    img = Image.new("RGB", size)
    for x in range(size[0]):
        for y in range(size[1]):
            img.putpixel((x, y), (x * 8 % 256, y * 12 % 256, (x + y) * 5 % 256))
    return img


def max_pixel_diff(a, b):
    diff = ImageChops.difference(a.convert("RGB"), b.convert("RGB"))
    return max(ext[1] for ext in diff.getextrema())


def test_jpeg_strips_exif_icc_and_applies_orientation(tmp, out_dir):
    src = os.path.join(tmp, "photo.jpg")
    original = gradient_image((30, 20))
    exif = Image.Exif()
    exif[274] = 6          # orientation: rotate 90 CW for display
    exif[271] = "TestCam"  # make
    original.save(src, exif=exif.tobytes(), icc_profile=b"FAKE-ICC-PROFILE")

    out = nullbit.clean_file(src, out_dir)

    assert os.path.basename(out) == "photo_nullbit.jpg", out
    cleaned = Image.open(out)
    assert list(cleaned.getexif()) == [], "EXIF survived"
    assert "icc_profile" not in cleaned.info, "ICC profile survived"
    with Image.open(src) as saved:
        expected = ImageOps.exif_transpose(saved)
    assert cleaned.size == expected.size == (20, 30), cleaned.size
    assert max_pixel_diff(cleaned, expected) <= 8, "pixels drifted or lost orientation"
    assert os.path.exists(src), "original was modified or removed"


def test_png_strips_text_chunks(tmp, out_dir):
    src = os.path.join(tmp, "gen.png")
    img = gradient_image((10, 10))
    meta = PngInfo()
    meta.add_text("prompt", "a cat in a hat")
    meta.add_text("parameters", "steps: 20")
    img.save(src, pnginfo=meta)

    out = nullbit.clean_file(src, out_dir)

    cleaned = Image.open(out)
    assert not cleaned.text, f"text chunks survived: {cleaned.text}"
    assert "prompt" not in cleaned.info and "parameters" not in cleaned.info
    assert list(cleaned.getdata()) == list(img.getdata()), "pixels changed"


def test_never_overwrites_previous_output(tmp, out_dir):
    src = os.path.join(tmp, "dup.png")
    Image.new("RGB", (5, 5), (9, 9, 9)).save(src)

    first = nullbit.clean_file(src, out_dir)
    second = nullbit.clean_file(src, out_dir)

    assert os.path.basename(first) == "dup_nullbit.png"
    assert os.path.basename(second) == "dup_nullbit_1.png"
    assert os.path.exists(first) and os.path.exists(second)


def test_corrupt_file_raises(out_dir):
    bad = os.path.join(out_dir, "broken.jpg")
    with open(bad, "wb") as f:
        f.write(b"not an image at all")

    try:
        nullbit.clean_file(bad, out_dir)
    except Exception:
        pass
    else:
        raise AssertionError("corrupt file did not raise")


def test_webp_strips_exif(tmp, out_dir):
    src = os.path.join(tmp, "shot.webp")
    img = gradient_image((12, 12))
    exif = Image.Exif()
    exif[274] = 1
    exif[271] = "TestCam"
    img.save(src, exif=exif.tobytes(), lossless=False)

    out = nullbit.clean_file(src, out_dir)

    cleaned = Image.open(out)
    assert list(cleaned.getexif()) == [], "EXIF survived in webp"


def test_save_clean_falls_back_to_supported_mode(out_dir):
    cmyk = Image.new("CMYK", (8, 8), (10, 20, 30, 40))
    cmyk_target = os.path.join(out_dir, "cmyk_as.png")
    nullbit.save_clean(cmyk, cmyk_target)
    assert Image.open(cmyk_target).mode == "RGB"

    rgba = Image.new("RGBA", (8, 8), (255, 0, 0, 128))
    jpg_target = os.path.join(out_dir, "rgba_as.jpg")
    nullbit.save_clean(rgba, jpg_target)
    assert Image.open(jpg_target).mode == "RGB"


def main():
    tmp = tempfile.mkdtemp(prefix="nullbit_test_")
    out_dir = os.path.join(tmp, "out")
    os.makedirs(out_dir)

    test_jpeg_strips_exif_icc_and_applies_orientation(tmp, out_dir)
    test_png_strips_text_chunks(tmp, out_dir)
    test_never_overwrites_previous_output(tmp, out_dir)
    test_corrupt_file_raises(out_dir)
    test_webp_strips_exif(tmp, out_dir)
    test_save_clean_falls_back_to_supported_mode(out_dir)

    print("OK: all cleaning checks passed")


if __name__ == "__main__":
    main()
