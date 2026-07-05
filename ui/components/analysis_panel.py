"""
Analysis Panel.

Displays AI insights for a selected recommendation.
"""

import streamlit as st

from ui.components.styles.chips import skill_chip
from ui.components.styles import theme


def render_analysis_panel(
    recommendation,
):
    """
    Render the AI Inspector.
    """

    theme.section("🤖 AI Inspector")

    if recommendation is None:

        st.info(
            """
Select a job and click **Analyze Resume**.

The recommendation details and AI explanation
will appear here.
"""
        )

        return

    # --------------------------------------------------
    # Recommendation Score
    # --------------------------------------------------

    st.metric(
        "Recommendation Score",
        f"{recommendation.score:.1f}%"
    )

    st.progress(
        recommendation.score / 100
    )

    theme.divider()

    # --------------------------------------------------
    # Skills
    # --------------------------------------------------

    left, right = st.columns(2)

    with left:

        theme.subsection(
            "✅ Matched Skills"
        )

        if recommendation.matched_skills:

            for skill in recommendation.matched_skills:

                skill_chip(
                    skill.name,
                    positive=True,
                )

        else:

            st.info(
                "No matched skills."
            )

    with right:

        theme.subsection(
            "❌ Missing Skills"
        )

        if recommendation.missing_skills:

            for skill in recommendation.missing_skills:

                skill_chip(
                    skill.name,
                    positive=False,
                )

        else:

            st.success(
                "No missing skills!"
            )

    theme.divider()

    # --------------------------------------------------
    # Recruiter Summary
    # --------------------------------------------------

    theme.subsection(
        "📝 Recruiter Summary"
    )

    if recommendation.recruiter_summary:

        st.write(
            recommendation.recruiter_summary
        )

    else:

        st.info(
            "No AI summary available."
        )

    theme.divider()

    # --------------------------------------------------
    # Recommendations
    # --------------------------------------------------

    theme.subsection(
        "🚀 Recommendations"
    )

    if recommendation.recommendations:

        for rec in recommendation.recommendations:

            st.write(f"• {rec}")

    else:

        st.info(
            "No recommendations."
        )

    theme.divider()

    # --------------------------------------------------
    # Signals
    # --------------------------------------------------

    theme.subsection(
        "📊 Recommendation Signals"
    )

    for signal in recommendation.signal_results:

        st.write(
            f"**{signal.signal_name}**"
        )

        st.progress(
            signal.score / 100
        )

        st.caption(
            signal.reason
        )