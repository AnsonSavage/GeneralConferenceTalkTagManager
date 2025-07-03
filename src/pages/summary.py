"""
Summary page module.
"""
import streamlit as st
from typing import List, Dict, Any


def render_summary_page(db) -> None:
    """Render the Summary page."""
    st.header("Project Summary")
    
    # Get statistics
    talks = db.get_talks_summary()
    all_tags = db.get_all_tags()
    keywords = db.get_keywords()
    
    # Display metrics
    _render_summary_metrics(talks, all_tags)
    
    # Display progress
    _render_progress_section(talks)
    
    # Display recent talks
    if talks:
        _render_recent_talks(talks)


def _render_summary_metrics(talks: List[Dict[str, Any]], all_tags: List[Dict[str, Any]]) -> None:
    """Render summary metrics."""
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Talks", len(talks))
    
    with col2:
        total_paragraphs = sum(talk['paragraph_count'] for talk in talks)
        st.metric("Total Paragraphs", total_paragraphs)
    
    with col3:
        total_reviewed = sum(talk['reviewed_count'] for talk in talks)
        st.metric("Reviewed Paragraphs", total_reviewed)
    
    with col4:
        st.metric("Total Tags", len(all_tags))


def _render_progress_section(talks: List[Dict[str, Any]]) -> None:
    """Render progress tracking section."""
    total_paragraphs = sum(talk['paragraph_count'] for talk in talks)
    total_reviewed = sum(talk['reviewed_count'] for talk in talks)
    
    if total_paragraphs > 0:
        progress = total_reviewed / total_paragraphs
        st.progress(progress)
        st.write(f"Review Progress: {progress:.1%}")


def _render_recent_talks(talks: List[Dict[str, Any]]) -> None:
    """Render recent talks section."""
    st.subheader("Recent Talks")
    recent_talks = talks[:5]  # Show first 5 (sorted by date DESC)
    
    for talk in recent_talks:
        st.markdown(f"**[{talk['title']}]({talk['hyperlink']})** - {talk['speaker']} ({talk['conference_date']})")
        st.markdown(f"Paragraphs: {talk['paragraph_count']}, Reviewed: {talk['reviewed_count']}")
        st.divider()