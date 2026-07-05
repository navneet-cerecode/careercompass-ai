"""
CareerCompass Design System.

Shared UI helpers for consistent styling across the application.
"""

import streamlit as st


def section(title: str) -> None:
    """
    Render a section heading.
    """

    st.markdown(f"## {title}")


def subsection(title: str) -> None:
    """
    Render a subsection heading.
    """

    st.markdown(f"### {title}")


def divider() -> None:
    """
    Render a divider.
    """

    st.divider()


def success(text: str) -> None:
    """
    Render success text.
    """

    st.success(text)


def error(text: str) -> None:
    """
    Render error text.
    """

    st.error(text)


def info(text: str) -> None:
    """
    Render info text.
    """

    st.info(text)


def caption(text: str) -> None:
    """
    Render caption.
    """

    st.caption(text)