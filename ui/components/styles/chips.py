"""
Reusable chip components.

Used throughout Solara Hire.
"""

import streamlit as st


def skill_chip(
    text: str,
    positive: bool = True,
) -> None:
    """
    Render a skill chip.
    """

    if positive:

        st.markdown(
            f"""
<div style="
display:inline-block;
padding:6px 12px;
margin:4px;
background:#d1fae5;
border-radius:20px;
font-size:14px;
font-weight:600;
color:#065f46;
">
✅ {text}
</div>
""",
            unsafe_allow_html=True,
        )

    else:

        st.markdown(
            f"""
<div style="
display:inline-block;
padding:6px 12px;
margin:4px;
background:#fee2e2;
border-radius:20px;
font-size:14px;
font-weight:600;
color:#991b1b;
">
❌ {text}
</div>
""",
            unsafe_allow_html=True,
        )
