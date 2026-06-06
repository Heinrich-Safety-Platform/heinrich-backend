import io
import os
import uuid
from pathlib import Path

from PIL import Image
from PIL.ExifTags import GPSTAGS


class ImageService:
    def save_image(self, contents: bytes, filename: str) -> str:
        upload_dir = os.getenv("UPLOAD_DIR", "uploads")
        os.makedirs(upload_dir, exist_ok=True)

        ext = Path(filename).suffix
        unique_name = f"{uuid.uuid4()}{ext}"
        dest = os.path.join(upload_dir, unique_name)

        with open(dest, "wb") as f:
            f.write(contents)

        return dest

    def extract_exif(self, contents: bytes) -> dict:
        try:
            image = Image.open(io.BytesIO(contents))
            gps_ifd = image.getexif().get_ifd(0x8825)
            if not gps_ifd:
                return {}

            return {GPSTAGS.get(tag_id, tag_id): value for tag_id, value in gps_ifd.items()}
        except Exception:
            return {}
