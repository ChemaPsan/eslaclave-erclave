import base64
import importlib
import io
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest
from PIL import Image
from pydantic import ValidationError
from erclave_common.errors import ErclaveError

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
for name in list(sys.modules):
    if name=="app" or name.startswith("app."):del sys.modules[name]
files=importlib.import_module("app.evidence_files")
schemas=importlib.import_module("app.schemas")


def upload(name,data):return schemas.ServiceEvidenceFileRequest(filename=name,content_base64=base64.b64encode(data).decode())


@pytest.mark.parametrize("format,ext",[("JPEG","jpg"),("PNG","png"),("WEBP","webp"),("HEIF","heic")])
def test_photos_are_optimized_and_metadata_removed(format,ext):
    photo=Image.new("RGB",(3000,2000),(80,130,200));source=io.BytesIO()
    exif=Image.Exif();exif[315]="Private camera owner";exif[274]=6
    photo.save(source,format=format,exif=exif)
    result=files.normalize_file(upload("camera."+ext,source.getvalue()))
    assert result["filename"]=="camera.webp" and result["media_type"]=="image/webp"
    assert 0<len(result["data"])<=300*1024
    with Image.open(io.BytesIO(result["data"])) as optimized:
        assert max(optimized.size)<=1600 and not optimized.getexif()


@pytest.mark.parametrize("name,body",[("fake.jpg",b"not an image"),("bad.pdf",b"bad"),("program.exe",b"MZ"),("bad.txt",b"\x00"),("big.txt",b"x"*(2*1024*1024+1)),("big.jpg",b"x"*(5*1024*1024+1))],ids=["fake-image","fake-pdf","executable","invalid-text","big-document","big-photo"])
def test_invalid_and_oversized_files_rejected(name,body):
    with pytest.raises((ErclaveError,ValidationError)):files.normalize_file(upload(name,body))


def test_evidence_request_requires_written_description_and_bounds_files():
    with pytest.raises(ValidationError):schemas.ServiceEvidenceRequest(description="   ")
    with pytest.raises(ValidationError):schemas.ServiceEvidenceRequest(description="Reception",files=[upload("a.txt",b"a")]*4)
    assert schemas.ServiceEvidenceRequest(description="  Received intact  ").description=="Received intact"


def test_private_store_rejects_path_traversal(tmp_path,monkeypatch):
    monkeypatch.setattr(files,"get_settings",lambda:SimpleNamespace(environment="local"))
    store=files.PrivateEvidenceStore();store.root=tmp_path
    with pytest.raises(ValueError):store.put("../../outside",b"x","text/plain")
    key="a"*64+"/"+"b"*32
    store.put(key,b"evidence","text/plain");assert store.read(key)==b"evidence"
    with pytest.raises(FileExistsError):store.put(key,b"different","text/plain")
    assert store.read(key)==b"evidence"
    store.delete(key);store.delete(key);assert not store.path(key).exists()


def test_local_retention_deletes_old_objects_but_keeps_fresh(tmp_path,monkeypatch):
    import os,time
    monkeypatch.setattr(files,"get_settings",lambda:SimpleNamespace(environment="local"))
    store=files.PrivateEvidenceStore();store.root=tmp_path
    old="a"*64+"/"+"b"*32;fresh="a"*64+"/"+"c"*32
    store.put(old,b"old","text/plain");store.put(fresh,b"fresh","text/plain")
    past=time.time()-366*86400;os.utime(store.path(old),(past,past))
    store.purge_local_expired_objects()
    assert not store.path(old).exists() and store.read(fresh)==b"fresh"


def test_cloud_store_refuses_policy_that_retains_versions_without_network(monkeypatch):
    from google.cloud import storage as gcs
    monkeypatch.setattr(files,"get_settings",lambda:SimpleNamespace(environment="qa"))
    monkeypatch.setenv("ERCLAVE_EVIDENCE_BUCKET","unit-test-only")
    bucket=SimpleNamespace(lifecycle_rules=[{"action":{"type":"Delete"},"condition":{"age":365}}],retention_period=None,default_event_based_hold=False,versioning_enabled=True,soft_delete_policy=SimpleNamespace(retention_duration_seconds=0),iam_configuration=SimpleNamespace(uniform_bucket_level_access_enabled=True,public_access_prevention="enforced"))
    monkeypatch.setattr(gcs,"Client",lambda:SimpleNamespace(get_bucket=lambda name:bucket))
    with pytest.raises(ErclaveError):files.PrivateEvidenceStore()
    bucket.versioning_enabled=False
    assert not files.PrivateEvidenceStore().local


@pytest.mark.parametrize("rules",[
    [],
    [{"action":{"type":"Delete"},"condition":{"age":364}}],
    [{"action":{"type":"Delete"},"condition":{"age":366}}],
    [{"action":{"type":"Delete"},"condition":{"age":365,"matchesPrefix":["partial/"]}}],
    [{"action":{"type":"Delete"},"condition":{"age":365}},
     {"action":{"type":"Delete"},"condition":{"age":1}}],
],ids=["missing","early","late","partial-coverage","extra-early-delete"])
def test_cloud_store_requires_only_complete_365_day_lifecycle(monkeypatch,rules):
    from google.cloud import storage as gcs
    monkeypatch.setattr(files,"get_settings",lambda:SimpleNamespace(environment="qa"))
    monkeypatch.setenv("ERCLAVE_EVIDENCE_BUCKET","unit-test-only")
    bucket=SimpleNamespace(lifecycle_rules=rules,retention_period=None,default_event_based_hold=False,versioning_enabled=False,soft_delete_policy=SimpleNamespace(retention_duration_seconds=0),iam_configuration=SimpleNamespace(uniform_bucket_level_access_enabled=True,public_access_prevention="enforced"))
    monkeypatch.setattr(gcs,"Client",lambda:SimpleNamespace(get_bucket=lambda name:bucket))
    with pytest.raises(ErclaveError) as error:files.PrivateEvidenceStore()
    assert error.value.code=="service_evidence_storage_unavailable"


@pytest.mark.parametrize("setting,value",[
    ("retention_period",86400),
    ("default_event_based_hold",True),
    ("soft_delete",604800),
    ("uniform_access",False),
    ("public_access","inherited"),
],ids=["retention-lock","default-hold","default-soft-delete","object-acls","public-not-enforced"])
def test_cloud_store_refuses_retention_or_privacy_drift(monkeypatch,setting,value):
    from google.cloud import storage as gcs
    monkeypatch.setattr(files,"get_settings",lambda:SimpleNamespace(environment="qa"))
    monkeypatch.setenv("ERCLAVE_EVIDENCE_BUCKET","unit-test-only")
    bucket=SimpleNamespace(lifecycle_rules=[{"action":{"type":"Delete"},"condition":{"age":365}}],retention_period=None,default_event_based_hold=False,versioning_enabled=False,soft_delete_policy=SimpleNamespace(retention_duration_seconds=0),iam_configuration=SimpleNamespace(uniform_bucket_level_access_enabled=True,public_access_prevention="enforced"))
    if setting=="soft_delete":bucket.soft_delete_policy.retention_duration_seconds=value
    elif setting=="uniform_access":bucket.iam_configuration.uniform_bucket_level_access_enabled=value
    elif setting=="public_access":bucket.iam_configuration.public_access_prevention=value
    else:setattr(bucket,setting,value)
    monkeypatch.setattr(gcs,"Client",lambda:SimpleNamespace(get_bucket=lambda name:bucket))
    with pytest.raises(ErclaveError) as error:files.PrivateEvidenceStore()
    assert error.value.code=="service_evidence_storage_unavailable"
