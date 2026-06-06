import io
import os
import uuid
from pathlib import Path

from PIL import Image
from PIL.ExifTags import GPSTAGS, TAGS


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
            raw_exif = image._getexif()
            if raw_exif is None:
                return {}

            gps_info = {}
            for tag_id, value in raw_exif.items():
                tag = TAGS.get(tag_id)
                if tag == "GPSInfo":
                    for gps_tag_id, gps_value in value.items():
                        gps_tag = GPSTAGS.get(gps_tag_id, gps_tag_id)
                        gps_info[gps_tag] = gps_value
                    break

            return gps_info
        except Exception:
            return {}
