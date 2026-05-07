import os
from pathlib import Path
from celery_app import celery
from PIL import Image

UPLOAD_DIR = Path("uploads")
OUTPUT_DIR = Path("compressed")

UPLOAD_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

TARGET_HEIGHT = 144


@celery.task(bind=True, name="compress_image")
def compress_image(self, filename: str) -> dict:
    input_path = UPLOAD_DIR / filename
    output_filename = f"compressed_{filename}"
    output_path = OUTPUT_DIR / output_filename

    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {filename}")

    self.update_state(state="PROGRESS", meta={"step": "opening image"})

    with Image.open(input_path) as img:
        original_width, original_height = img.size
        aspect_ratio = original_width / original_height
        new_height = TARGET_HEIGHT
        new_width = int(new_height * aspect_ratio)

        # Ensure dimensions are even (required by some formats)
        new_width = new_width if new_width % 2 == 0 else new_width + 1

        self.update_state(state="PROGRESS", meta={"step": "resizing image"})
        resized = img.resize((new_width, new_height), Image.LANCZOS)

        # Convert RGBA to RGB if saving as JPEG
        if output_filename.lower().endswith((".jpg", ".jpeg")) and resized.mode in ("RGBA", "P"):
            resized = resized.convert("RGB")

        self.update_state(state="PROGRESS", meta={"step": "saving image"})
        resized.save(output_path, optimize=True, quality=85)

    return {
        "original_filename": filename,
        "compressed_filename": output_filename,
        "original_size": (original_width, original_height),
        "compressed_size": (new_width, new_height),
        "output_path": str(output_path),
    }
