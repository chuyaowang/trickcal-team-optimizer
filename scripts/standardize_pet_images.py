"""Standardize pet icons and generate thumbnails.

The pet icon set is stored as WebP data under a .png filename (the game export
convention): 48 of the icons are already 300x300 lossy WebP at ~8-22KB, while a
few are oversized true-PNG screenshots. This script makes every master a square
MASTER_SIZE WebP and emits a small WebP thumbnail for each.

Rules:
  * A master already square at MASTER_SIZE *and* already WebP is copied
    byte-for-byte (no re-encode -> no quality loss, no git churn).
  * Anything else (non-square, or a true-PNG screenshot) is centered on a
    transparent square canvas (no crop/distortion), resized with LANCZOS only
    when needed, and saved as WebP at MASTER_QUALITY.
  * Thumbnails are THUMB_SIZE WebP at THUMB_QUALITY, generated for every icon.

Files keep their .png extension to match the csv `<id>.png` references and the
existing data set; the bytes are WebP, exactly like the current 48 icons.

By default output goes to a scratch OUT_DIR so it can be inspected WITHOUT
touching originals. Pass --in-place to write into data/pet_images once verified.

    /opt/miniconda3/envs/microsam/bin/python -m scripts.standardize_pet_images
    /opt/miniconda3/envs/microsam/bin/python -m scripts.standardize_pet_images --in-place
"""

import argparse
import glob
import os
import shutil

from PIL import Image

IMAGE_DIR = os.path.join("data", "pet_images")
# Thumbnails are served statically by the web app, so they live next to it.
THUMB_DIR = os.path.join("src", "ui", "static", "pet_thumbs")
OUT_DIR = "/tmp/pet_std"
MASTER_SIZE = 300
THUMB_SIZE = 96
MASTER_QUALITY = 90
THUMB_QUALITY = 85
WEBP_METHOD = 6  # 0-6, higher = slower/smaller


def is_webp(path: str) -> bool:
    with open(path, "rb") as f:
        return f.read(4) == b"RIFF"


def pad_to_square(im: Image.Image) -> Image.Image:
    """Center `im` on a transparent square canvas of side max(w, h)."""
    w, h = im.size
    side = max(w, h)
    canvas = Image.new("RGBA", (side, side), (0, 0, 0, 0))
    canvas.paste(im, ((side - w) // 2, (side - h) // 2))
    return canvas


def save_webp(im: Image.Image, path: str, quality: int) -> None:
    im.save(path, format="WEBP", quality=quality, method=WEBP_METHOD)


def build_master(src: str, dst: str) -> Image.Image:
    """Write the standardized master to `dst`; return its RGBA image.

    Returns the kept/produced master image (used to derive the thumbnail).
    """
    im = Image.open(src).convert("RGBA")
    if im.size == (MASTER_SIZE, MASTER_SIZE) and is_webp(src):
        if os.path.abspath(src) != os.path.abspath(dst):
            shutil.copyfile(src, dst)
        return im

    square = pad_to_square(im)
    if square.size != (MASTER_SIZE, MASTER_SIZE):
        square = square.resize((MASTER_SIZE, MASTER_SIZE), Image.LANCZOS)
    save_webp(square, dst, MASTER_QUALITY)
    return square


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--in-place", action="store_true",
                    help="write into data/pet_images instead of the scratch dir")
    args = ap.parse_args()

    if args.in_place:
        master_dir = IMAGE_DIR
        thumb_dir = THUMB_DIR
    else:
        master_dir = os.path.join(OUT_DIR, "masters")
        thumb_dir = os.path.join(OUT_DIR, "thumbnails")
    os.makedirs(master_dir, exist_ok=True)
    os.makedirs(thumb_dir, exist_ok=True)

    paths = sorted(glob.glob(os.path.join(IMAGE_DIR, "*.png")))
    mode = "IN-PLACE" if args.in_place else f"DRY-RUN -> {OUT_DIR}"
    print(f"[{mode}] {len(paths)} icon(s) -> {MASTER_SIZE}px WebP master "
          f"(q{MASTER_QUALITY}), {THUMB_SIZE}px WebP thumb (q{THUMB_QUALITY})\n")

    reencoded = 0
    for src in paths:
        name = os.path.basename(src)
        src_dims = Image.open(src).size
        src_kb = os.path.getsize(src) / 1024
        was_webp = is_webp(src)

        master_dst = os.path.join(master_dir, name)
        master = build_master(src, master_dst)

        thumb = master.resize((THUMB_SIZE, THUMB_SIZE), Image.LANCZOS)
        # served statically as <id>.webp (true extension -> correct content-type)
        thumb_dst = os.path.join(thumb_dir, os.path.splitext(name)[0] + ".webp")
        save_webp(thumb, thumb_dst, THUMB_QUALITY)

        out_kb = os.path.getsize(master_dst) / 1024
        thumb_kb = os.path.getsize(thumb_dst) / 1024
        kept = src_dims == (MASTER_SIZE, MASTER_SIZE) and was_webp
        if kept:
            print(f"  {name:>14}  kept ({out_kb:5.1f}KB)  thumb {thumb_kb:4.1f}KB")
        else:
            reencoded += 1
            tag = "" if was_webp else " [was PNG]"
            print(f"  {name:>14}  {src_dims[0]}x{src_dims[1]} {src_kb:6.1f}KB "
                  f"-> WebP {MASTER_SIZE}sq {out_kb:5.1f}KB  "
                  f"thumb {thumb_kb:4.1f}KB{tag}")

    print(f"\nMasters re-encoded: {reencoded}/{len(paths)} "
          f"(rest copied unchanged); thumbnails: {len(paths)}.")
    if not args.in_place:
        print(f"Inspect: {master_dir} and {thumb_dir}")
        print("Re-run with --in-place once verified.")


if __name__ == "__main__":
    main()