"""
Job Card Component.

Displays a single recommended job.
"""

import streamlit as st


def render_job_card(
    recommendation,
    resume,
    compass,
):
    """
    Render a recommended job.
    """

    job = recommendation.job

    with st.container(border=True):

        # --------------------------------------------------
        # Header
        # --------------------------------------------------

        left, center, right = st.columns([5, 2, 1])

        with left:

            st.subheader(job.title)

            st.write(f"🏢 **{job.company}**")

            st.write(f"📍 {job.location}")

        with center:

            score = recommendation.score

            stars = round(score / 20)

            st.markdown(
                f"### {'⭐' * stars}"
            )

            st.metric(
                "Match",
                f"{score:.1f}%"
            )

        with right:

            st.success("LIVE")

        # --------------------------------------------------
        # Description
        # --------------------------------------------------

        if job.description:

            st.write(job.description)

        # --------------------------------------------------
        # Skill Chips
        # --------------------------------------------------

        if recommendation.matched_skills:

            st.markdown("##### ✅ Matched Skills")

            cols = st.columns(4)

            for i, skill in enumerate(
                recommendation.matched_skills
            ):

                cols[i % 4].success(
                    skill.name
                )

        if recommendation.missing_skills:

            st.markdown("##### ⚠ Missing Skills")

            cols = st.columns(4)

            for i, skill in enumerate(
                recommendation.missing_skills
            ):

                cols[i % 4].warning(
                    skill.name
                )

        st.divider()

        # --------------------------------------------------
        # Buttons
        # --------------------------------------------------

        col1, col2 = st.columns(2)

        with col1:

            st.link_button(
                "🔗 View Job",
                str(job.url),
                use_container_width=True,
            )

        with col2:

            analyze = st.button(
                "🤖 AI Inspector",
                key=f"analyze_{job.id}",
                disabled=resume is None,
                use_container_width=True,
            )

        # --------------------------------------------------
        # AI Explanation
        # --------------------------------------------------

        if analyze:

            with st.spinner(
                "Generating recruiter insights..."
            ):

                try:

                    # This already returns a fully populated
                    # JobRecommendation
                    result = compass.analyze_resume(
                        resume,
                        job,
                    )

                    # Save the FULL result
                    st.session_state.selected_result = result

                    st.session_state.selected_job = (
                        result.job
                    )

                    st.rerun()

                except Exception as e:

                    st.error(
                        "Failed to analyze resume."
                    )

                    st.exception(e)