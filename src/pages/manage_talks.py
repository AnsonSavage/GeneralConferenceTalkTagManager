"""
Manage Talks page module.
"""
import streamlit as st
import pandas as pd
from typing import List, Dict, Any
from ..database.base_database import BaseDatabaseInterface  


def render_manage_talks_page(database: BaseDatabaseInterface) -> None:
    """Render the Manage Talks page."""
    st.header("Talks in Database")
    st.info("💡 Talks are automatically added to the database when you search for keywords. Only talks with matching paragraphs are stored.")
    
    # Display existing talks
    st.subheader("Talks with Keyword Matches")
    talks = database.get_talks_summary()
    
    if talks:
        _render_talks_table(talks)
        _render_keyword_usage_metrics(database)
    else:
        st.info("No talks in database yet. Start by searching for keywords to populate the database with matching content.")


def _render_talks_table(talks: List[Dict[str, Any]]) -> None:
    """Render the talks data table."""
    df = pd.DataFrame(talks)
    
    # Make hyperlinks clickable
    df['hyperlink'] = df['hyperlink'].apply(lambda x: f"[Link]({x})")
    
    st.dataframe(
        df,
        column_config={
            "hyperlink": st.column_config.LinkColumn("Link"),
            "paragraph_count": "Paragraphs",
            "reviewed_count": "Reviewed"
        },
        use_container_width=True
    )


def _render_keyword_usage_metrics(database: BaseDatabaseInterface) -> None:
    """Render keyword usage metrics."""
    st.subheader("Keyword Usage")
    
    keyword_usage = database.get_keyword_usage_statistics()
    
    if keyword_usage:
        cols = st.columns(3)
        for i, stat in enumerate(keyword_usage):
            keyword = stat['keyword']
            count = stat['usage_count']
            with cols[i % 3]:
                st.metric(keyword, count, help=f"Found in {count} paragraphs")