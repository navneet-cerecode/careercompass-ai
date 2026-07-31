import tempfile
from pathlib import Path

import streamlit as st


def _load_uploaded_resume(compass, uploaded):
    """Parse an uploaded resume and always remove its temporary file."""
    suffix = Path(uploaded.name).suffix.lower()
    temp_path = None

    try:
        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=suffix,
        ) as temp:
            temp_path = Path(temp.name)
            temp.write(uploaded.read())

        return compass.load_resume(str(temp_path))
    finally:
        if temp_path is not None:
            temp_path.unlink(missing_ok=True)


def render_resume_upload(compass):

    uploaded = st.file_uploader(
        "📄 Upload Resume",
        type=["pdf", "docx", "txt"],
    )

    if uploaded is None:
        return None

    if (
        st.session_state.resume is not None
        and st.session_state.get("uploaded_name") == uploaded.name
    ):
        return None

    resume = _load_uploaded_resume(
        compass,
        uploaded,
    )

    st.session_state.uploaded_name = uploaded.name

    return resume
