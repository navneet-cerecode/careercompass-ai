from io import BytesIO
from pathlib import Path

import pytest

from ui.components.resume_upload import _load_uploaded_resume


class UploadedResume(BytesIO):
    def __init__(self, content: bytes, name: str):
        super().__init__(content)
        self.name = name


class RecordingCompass:
    def __init__(self, *, fail: bool = False):
        self.fail = fail
        self.received_path = None

    def load_resume(self, path: str):
        self.received_path = Path(path)
        assert self.received_path.exists()
        if self.fail:
            raise RuntimeError("parse failed")
        return "parsed resume"


def test_uploaded_resume_temporary_file_is_removed_after_success():
    compass = RecordingCompass()
    uploaded = UploadedResume(b"Ada Lovelace\nPython", "resume.txt")

    result = _load_uploaded_resume(compass, uploaded)

    assert result == "parsed resume"
    assert compass.received_path is not None
    assert not compass.received_path.exists()


def test_uploaded_resume_temporary_file_is_removed_after_failure():
    compass = RecordingCompass(fail=True)
    uploaded = UploadedResume(b"invalid", "resume.txt")

    with pytest.raises(RuntimeError, match="parse failed"):
        _load_uploaded_resume(compass, uploaded)

    assert compass.received_path is not None
    assert not compass.received_path.exists()
