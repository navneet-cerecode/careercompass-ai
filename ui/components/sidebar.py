import streamlit as st


def render_sidebar():
    """
    Render the application sidebar.
    """

    with st.sidebar:

        st.title("🚀 CareerCompass AI")

        st.caption("AI-Powered Resume & Job Matching")

        st.markdown("---")

        role = st.selectbox(
            "🎯 Target Role",
            [
                "Machine Learning Engineer",
                "Data Scientist",
                "Data Engineer",
                "Deep Learning Engineer",
            ],
        )

        location = st.text_input(
            "📍 Location",
            value="India",
        )

        search = st.button(
            "🔍 Search Jobs",
            use_container_width=True,
        )

        st.markdown("---")

        st.markdown("### 🌐 Job Sources")

        st.write("• NVIDIA Careers")
        st.write("• JSearch API")
        st.write("• 1000+ Company Listings")

        st.markdown("---")

        st.markdown("### 🤖 AI Features")

        st.write("✓ Resume Parsing")
        st.write("✓ Semantic Matching")
        st.write("✓ AI Recruiter Review")
        st.write("✓ Skill Gap Analysis")

        st.markdown("---")

        st.caption("CareerCompass AI • Prototype")

    return role, location, search