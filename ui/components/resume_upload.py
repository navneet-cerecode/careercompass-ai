import tempfile

import streamlit as st


def render_resume_upload(compass):

    uploaded = st.file_uploader(
        "📄 Upload Resume",
        type=["pdf", "docx", "txt"],
    )

    if uploaded is None:
        return None

    if (
        st.session_state.resume is not None
        and st.session_state.get("uploaded_name")
        == uploaded.name
    ):
        return None

    suffix = "." + uploaded.name.split(".")[-1]

    with tempfile.NamedTemporaryFile(
        delete=False,
        suffix=suffix,
    ) as temp:

        temp.write(uploaded.read())

        path = temp.name

    resume = compass.load_resume(path)

    st.session_state.uploaded_name = uploaded.name

    return resume