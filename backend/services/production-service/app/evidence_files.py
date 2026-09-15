"""Bounded decoding, image optimization, private storage and attachment retention."""
import base64
import hashlib
import io
import os
import re
import warnings
import time
from pathlib import Path
from zipfile import ZipFile, BadZipFile

from PIL import Image, ImageOps, UnidentifiedImageError
from pillow_heif import register_heif_opener
from erclave_common.config import get_settings
from erclave_common.errors import ErclaveError

register_heif_opener()
Image.MAX_IMAGE_PIXELS = 20_000_000
MAX_IMAGE_INPUT = 5 * 1024 * 1024
MAX_DOCUMENT = 2 * 1024 * 1024
MAX_PHOTO = 300 * 1024


def reject(code="service_evidence_file_invalid"):
    raise ErclaveError(code, "Service evidence attachment rejected.", status_code=422)


def normalize_file(item):
    try:
        raw = base64.b64decode(item.content_base64, validate=True)
    except (ValueError, TypeError):
        reject()
    if not raw or len(raw) > MAX_IMAGE_INPUT: reject("service_evidence_file_too_large")
    name = re.sub(r"[^\w .()-]", "_", Path(item.filename.replace("\\", "/")).name, flags=re.UNICODE)[:160] or "attachment"
    suffix = Path(name).suffix.lower()
    if suffix in {".jpg", ".jpeg", ".png", ".webp", ".heic", ".heif", ".bmp", ".tif", ".tiff"}:
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("error", Image.DecompressionBombWarning)
                with Image.open(io.BytesIO(raw)) as original:
                    if original.width * original.height > 20_000_000 or getattr(original,"n_frames",1) != 1: reject()
                    photo = ImageOps.exif_transpose(original).convert("RGB")
                    photo.thumbnail((1600,1600), Image.Resampling.LANCZOS)
                    # A fresh image prevents EXIF/GPS/ICC/comments from being copied.
                    clean = Image.new("RGB", photo.size)
                    clean.paste(photo)
                    for edge in (1600,1280,1024,800,640):
                        clean.thumbnail((edge,edge),Image.Resampling.LANCZOS)
                        for quality in (80,65,50):
                            output=io.BytesIO(); clean.save(output,format="WEBP",quality=quality,method=4)
                            if output.tell() <= MAX_PHOTO:
                                return {"filename":Path(name).stem+".webp","media_type":"image/webp","data":output.getvalue()}
        except (UnidentifiedImageError, OSError, ValueError, Image.DecompressionBombWarning, Image.DecompressionBombError):
            reject()
        reject("service_evidence_file_too_large")
    if len(raw) > MAX_DOCUMENT: reject("service_evidence_file_too_large")
    media = {".pdf":"application/pdf", ".txt":"text/plain", ".docx":"application/vnd.openxmlformats-officedocument.wordprocessingml.document", ".xlsx":"application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"}.get(suffix)
    if not media: reject()
    if suffix == ".pdf" and (not raw.startswith(b"%PDF-") or b"%%EOF" not in raw[-2048:]): reject()
    if suffix == ".txt":
        try: raw.decode("utf-8")
        except UnicodeDecodeError: reject()
        if b"\x00" in raw: reject()
    if suffix in {".docx", ".xlsx"}:
        try:
            with ZipFile(io.BytesIO(raw)) as archive:
                entries=archive.infolist()
                if len(entries)>2000 or sum(entry.file_size for entry in entries)>20*1024*1024: reject()
                names={entry.filename for entry in entries}
                needed="word/document.xml" if suffix==".docx" else "xl/workbook.xml"
                if "[Content_Types].xml" not in names or needed not in names or any("vbaproject" in name.lower() for name in names): reject()
        except (BadZipFile, OSError): reject()
    return {"filename":name,"media_type":media,"data":raw}


class PrivateEvidenceStore:
    def __init__(self):
        self.local = get_settings().environment == "local"
        if self.local:
            self.root = Path(__file__).resolve().parents[4] / ".local" / "service-evidence"
        else:
            from google.cloud import storage
            name=os.getenv("ERCLAVE_EVIDENCE_BUCKET", "")
            if not name: raise ErclaveError("service_evidence_storage_unavailable", "Private evidence storage must be configured.", status_code=503)
            self.bucket=storage.Client().get_bucket(name)
            # Retention is enforced even when Cloud Run is scaled to zero.
            # A dedicated bucket must not also contain a rule that deletes earlier.
            valid=list(self.bucket.lifecycle_rules)==[{"action":{"type":"Delete"},"condition":{"age":365}}]
            if not valid or self.bucket.retention_period or self.bucket.default_event_based_hold or not self.bucket.iam_configuration.uniform_bucket_level_access_enabled or self.bucket.versioning_enabled or self.bucket.soft_delete_policy.retention_duration_seconds or self.bucket.iam_configuration.public_access_prevention != "enforced":
                raise ErclaveError("service_evidence_storage_unavailable", "Private bucket must enforce 365-day deletion without retained versions.",status_code=503)

    def path(self,key):
        if not re.fullmatch(r"[a-f0-9]{64}/[a-f0-9]{32}",key): raise ValueError("invalid_evidence_object_key")
        return self.root / key

    def put(self,key,data,media_type):
        if self.local:
            path=self.path(key);path.parent.mkdir(parents=True,exist_ok=True)
            output=path.open("xb")
            try:
                with output: output.write(data)
            except Exception:
                path.unlink(missing_ok=True);raise
        else: self.bucket.blob(key).upload_from_string(data,content_type=media_type,if_generation_match=0)

    def read(self,key):
        if self.local:return self.path(key).read_bytes()
        from google.api_core.exceptions import NotFound
        try:return self.bucket.blob(key).download_as_bytes()
        except NotFound as exc:raise FileNotFoundError(key) from exc

    def delete(self,key):
        if self.local:self.path(key).unlink(missing_ok=True)
        else:
            from google.api_core.exceptions import NotFound
            try:self.bucket.blob(key).delete()
            except NotFound:pass

    def purge_local_expired_objects(self):
        if not self.local or not self.root.exists():return
        cutoff=time.time()-365*86400
        for path in self.root.glob("*/*"):
            key=path.relative_to(self.root).as_posix()
            if re.fullmatch(r"[a-f0-9]{64}/[a-f0-9]{32}",key) and path.is_file() and path.stat().st_mtime<=cutoff:
                self.delete(key)
