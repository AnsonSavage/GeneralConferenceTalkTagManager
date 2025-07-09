"""
Filter controls component for the Conference Talks Analysis application.
"""
import streamlit as st
from typing import Dict, Any
from ..database.base_database import BaseDatabaseInterface


class FilterControls:
    """Component for rendering filter controls."""
    
    def __init__(self, db: BaseDatabaseInterface):
        self.db = db
        
    def render_paragraph_filters(self) -> Dict[str, Any]:
        """Render paragraph filtering controls."""
        with st.expander("🔍 Filter Options", expanded=True):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                # Tag filter
                all_tags = self.db.get_all_tags()
                tag_options = ["All Tags", "No Tags"] + [tag['name'] for tag in all_tags]
                selected_tag_filter = st.selectbox(
                    "Filter by Tag:",
                    options=tag_options,
                    index=1,  # Default to "No Tags"
                    help="Filter paragraphs by tag assignment"
                )
            
            with col2:
                # Keyword filter
                keywords = self.db.get_keywords()
                keyword_options = ["All Keywords"] + keywords
                selected_keyword_filter = st.selectbox(
                    "Filter by Keyword:",
                    options=keyword_options,
                    help="Filter paragraphs by keyword matches"
                )
            
            with col3:
                # Additional filters
                show_reviewed = st.checkbox(
                    "Include Reviewed", 
                    value=False,
                    help="Include paragraphs that have been reviewed"
                )
        
        # Process filters
        if selected_tag_filter == "All Tags":
            tag_filter = None
            untagged_only = False
        elif selected_tag_filter == "No Tags":
            tag_filter = None
            untagged_only = True
        else:
            tag_filter = selected_tag_filter
            untagged_only = False
        
        keyword_filter = selected_keyword_filter if selected_keyword_filter != "All Keywords" else None
        
        return {
            'tag_filter': tag_filter,
            'keyword_filter': keyword_filter,
            'untagged_only': untagged_only,
            'show_reviewed': show_reviewed
        }
    
    def render_comprehensive_paragraph_filters(self) -> Dict[str, Any]:
        """Render comprehensive paragraph filtering controls for management interface."""
        with st.expander("🔍 Advanced Filter Options", expanded=True):
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                # Tag filter
                all_tags = self.db.get_all_tags()
                tag_options = ["All Tags", "No Tags"] + [tag['name'] for tag in all_tags]
                selected_tag_filter = st.selectbox(
                    "Filter by Tag:",
                    options=tag_options,
                    help="Filter paragraphs by tag assignment"
                )
            
            with col2:
                # Keyword filter
                keywords = self.db.get_keywords()
                keyword_options = ["All Keywords"] + keywords
                selected_keyword_filter = st.selectbox(
                    "Filter by Keyword:",
                    options=keyword_options,
                    help="Filter paragraphs by keyword matches"
                )
            
            with col3:
                # Review status filter
                review_filter = st.selectbox(
                    "Review Status:",
                    options=["All", "Reviewed Only", "Unreviewed Only"],
                    help="Filter by review status"
                )
            
            with col4:
                # Date range filter
                conference_years = ["All Years"] + [str(year) for year in range(2000, 2026)]
                selected_year = st.selectbox(
                    "Conference Year:",
                    options=conference_years,
                    help="Filter by conference year"
                )
        
        # Process filters
        if selected_tag_filter == "All Tags":
            tag_filter = None
            untagged_only = False
        elif selected_tag_filter == "No Tags":
            tag_filter = None
            untagged_only = True
        else:
            tag_filter = selected_tag_filter
            untagged_only = False
        
        keyword_filter = selected_keyword_filter if selected_keyword_filter != "All Keywords" else None
        
        reviewed_only = None
        if review_filter == "Reviewed Only":
            reviewed_only = True
        elif review_filter == "Unreviewed Only":
            reviewed_only = False
        
        return {
            'tag_filter': tag_filter,
            'keyword_filter': keyword_filter,
            'untagged_only': untagged_only,
            'reviewed_only': reviewed_only,
            'year_filter': selected_year if selected_year != "All Years" else None
        }