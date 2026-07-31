import os
import sys

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import streamlit as st

from core.career_compass import CareerCompass

from ui.components.analysis_panel import render_analysis_panel
from ui.components.header import render_header
from ui.components.job_card import render_job_card
from ui.components.resume_upload import render_resume_upload
from ui.components.sidebar import render_sidebar

# ======================================================
# Page Config
# ======================================================

st.set_page_config(
    page_title="CareerCompass AI",
    page_icon="🚀",
    layout="wide",
)

# ======================================================
# Session State
# ======================================================

if "resume" not in st.session_state:
    st.session_state.resume = None

if "recommendations" not in st.session_state:
    st.session_state.recommendations = []

if "searched" not in st.session_state:
    st.session_state.searched = False

if "selected_result" not in st.session_state:
    st.session_state.selected_result = None

# ======================================================
# Backend
# ======================================================


@st.cache_resource
def get_career_compass() -> CareerCompass:
    return CareerCompass()


compass = get_career_compass()

# ======================================================
# Header
# ======================================================

render_header()

# ======================================================
# Sidebar
# ======================================================

role, location, search = render_sidebar()

# ======================================================
# Resume Upload
# ======================================================

resume = render_resume_upload(compass)

if resume is not None:
    st.session_state.resume = resume

if st.session_state.resume is not None:
    st.success(f"✅ Resume Loaded: {st.session_state.resume.name}")

st.divider()

# ======================================================
# Search Jobs
# ======================================================

if search:
    if st.session_state.resume is None:
        st.warning("Please upload your resume before searching.")

    else:
        with st.spinner("Searching and ranking jobs..."):
            jobs = compass.search_jobs(
                role,
                location,
            )

            recommendations = compass.recommend_jobs(
                st.session_state.resume,
                jobs,
            )

            st.session_state.recommendations = recommendations

            st.session_state.searched = True

            st.session_state.selected_result = None

# ======================================================
# Workspace
# ======================================================

jobs_col, inspector_col = st.columns(
    [2.2, 1],
    gap="large",
)

# ======================================================
# LEFT : Ranked Jobs
# ======================================================

with jobs_col:
    if st.session_state.searched:
        st.subheader("🎯 Recommended Jobs")

        st.write(f"Showing **{len(st.session_state.recommendations)}** ranked jobs.")

        st.divider()

        for recommendation in st.session_state.recommendations:
            render_job_card(
                recommendation,
                st.session_state.resume,
                compass,
            )

# ======================================================
# RIGHT : AI Inspector
# ======================================================

with inspector_col:
    render_analysis_panel(st.session_state.selected_result)
