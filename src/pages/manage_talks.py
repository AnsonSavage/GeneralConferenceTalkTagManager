"""
Manage Talks page module.
"""
import streamlit as st
import pandas as pd
import sqlite3
from typing import List, Dict, Any


def render_manage_talks_page(db) -> None:
    """Render the Manage Talks page."""
    st.header("Talks in Database")
    st.info("💡 Talks are automatically added to the database when you search for keywords. Only talks with matching paragraphs are stored.")
    
    # Display existing talks
    st.subheader("Talks with Keyword Matches")
    talks = db.get_talks_summary()
    
    if talks:
        _render_talks_table(talks)
        _render_keyword_usage_metrics(db)
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


def _render_keyword_usage_metrics(db) -> None:
    """Render keyword usage metrics."""
    st.subheader("Keyword Usage")
    
    conn = sqlite3.connect(db.db_path)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT k.keyword, COUNT(DISTINCT pk.paragraph_id) as usage_count
        FROM keywords k
        JOIN paragraph_keywords pk ON k.id = pk.keyword_id
        GROUP BY k.keyword
        ORDER BY usage_count DESC
    """)
    
    keyword_usage = cursor.fetchall()
    conn.close()
    
    if keyword_usage:
        cols = st.columns(3)
        for i, (keyword, count) in enumerate(keyword_usage):
            with cols[i % 3]:
                st.metric(keyword, count, help=f"Found in {count} paragraphs")