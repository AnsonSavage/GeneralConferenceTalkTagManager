"""
Statistics page module - Shows tag tree hierarchy with usage statistics.
"""
import streamlit as st
from typing import Dict, List, Any, Set
from ..database.base_database import BaseDatabaseInterface


def render_statistics_page(database: BaseDatabaseInterface) -> None:
    """Render the Statistics page showing tag hierarchy with usage statistics."""
    st.header("📊 Tag Statistics")
    
    # Get tag usage statistics
    tag_stats = database.get_tag_usage_statistics()
    
    if not tag_stats:
        st.info("No tags found in the database.")
        return
    
    # Initialize session state for selected tags if not exists
    if 'selected_tags' not in st.session_state:
        # By default, all tags are selected
        st.session_state.selected_tags = {tag['id'] for tag in tag_stats}
    
    # Get total paragraph count for percentage calculations
    total_paragraphs = _get_total_paragraph_count(database)
    
    # Build tag hierarchy with statistics
    tag_dict = {tag['id']: tag for tag in tag_stats}
    root_tags = [tag for tag in tag_stats if tag['parent_tag_id'] is None]
    
    # Filter statistics based on selected tags
    filtered_stats = _filter_tag_statistics(tag_stats, st.session_state.selected_tags, database)
    filtered_total_paragraphs = _calculate_filtered_total_paragraphs(
        st.session_state.selected_tags, database
    )
    
    # Calculate descendant counts for filtered tags
    descendant_counts = _calculate_descendant_counts(filtered_stats, tag_dict, st.session_state.selected_tags)
    
    # Tag selection controls
    st.markdown("### 🎛️ Tag Selection")
    col1, col2, col3 = st.columns([1, 1, 2])
    
    with col1:
        if st.button("✅ Select All", help="Select all tags for statistics"):
            st.session_state.selected_tags = {tag['id'] for tag in tag_stats}
            st.rerun()
    
    with col2:
        if st.button("❌ Deselect All", help="Deselect all tags"):
            st.session_state.selected_tags = set()
            st.rerun()
    
    with col3:
        selected_count = len(st.session_state.selected_tags)
        total_count = len(tag_stats)
        st.markdown(f"**Selected:** {selected_count}/{total_count} tags")
    
    # Quick selection presets
    with st.expander("🔧 Quick Selection Presets", expanded=False):
        preset_col1, preset_col2 = st.columns(2)
        
        with preset_col1:
            if st.button("📊 Root Tags Only", help="Select only root-level tags"):
                st.session_state.selected_tags = {tag['id'] for tag in root_tags}
                st.rerun()
            
            if st.button("🌿 Leaf Tags Only", help="Select only tags with no children"):
                leaf_tags = _get_leaf_tags(tag_stats)
                st.session_state.selected_tags = {tag['id'] for tag in leaf_tags}
                st.rerun()
        
        with preset_col2:
            if st.button("🔥 Most Used (Top 10)", help="Select the 10 most used tags"):
                top_tags = sorted(tag_stats, key=lambda x: x['usage_count'], reverse=True)[:10]
                st.session_state.selected_tags = {tag['id'] for tag in top_tags}
                st.rerun()
            
            if st.button("📈 Used Tags Only", help="Select only tags with at least one paragraph"):
                used_tags = [tag for tag in tag_stats if tag['usage_count'] > 0]
                st.session_state.selected_tags = {tag['id'] for tag in used_tags}
                st.rerun()
    
    st.divider()
    
    # Statistics display
    st.markdown("### 🌳 Tag Hierarchy with Statistics")
    
    if len(st.session_state.selected_tags) == 0:
        st.warning("No tags selected. Please select at least one tag to view statistics.")
        return
    
    # Show filtered totals
    if filtered_total_paragraphs != total_paragraphs:
        st.markdown(f"**Total paragraphs (all tags):** {total_paragraphs}")
        st.markdown(f"**Total paragraphs (selected tags):** {filtered_total_paragraphs}")
        st.caption("Percentages are calculated based on selected tags only")
    else:
        st.markdown(f"**Total paragraphs in database:** {total_paragraphs}")
    
    if filtered_total_paragraphs > 0:
        st.divider()
        
        # Render each root tag and its hierarchy with checkboxes
        for i, root_tag in enumerate(root_tags):
            _render_tag_with_statistics_and_checkbox(
                root_tag, tag_dict, descendant_counts, filtered_total_paragraphs, 
                st.session_state.selected_tags, level=0
            )
            if i < len(root_tags) - 1:
                st.divider()
    else:
        st.warning("No paragraphs found for the selected tags.")


def _filter_tag_statistics(
    tag_stats: List[Dict], 
    selected_tag_ids: Set[int], 
    database: BaseDatabaseInterface
) -> List[Dict]:
    """Filter tag statistics to only include selected tags and their usage."""
    filtered_stats = []
    
    for tag in tag_stats:
        if tag['id'] in selected_tag_ids:
            # Keep the tag with its original usage count
            filtered_stats.append(tag.copy())
        else:
            # Include the tag but with zero usage for hierarchy display
            filtered_tag = tag.copy()
            filtered_tag['usage_count'] = 0
            filtered_stats.append(filtered_tag)
    
    return filtered_stats


def _calculate_filtered_total_paragraphs(selected_tag_ids: Set[int], database: BaseDatabaseInterface) -> int:
    """Calculate total unique paragraphs that have any of the selected tags."""
    if not selected_tag_ids:
        return 0
    
    unique_paragraph_ids = set()
    
    for tag_id in selected_tag_ids:
        paragraphs = database.get_paragraphs_by_tag(tag_id)
        unique_paragraph_ids.update(p['id'] for p in paragraphs)
    
    return len(unique_paragraph_ids)


def _get_leaf_tags(tag_stats: List[Dict]) -> List[Dict]:
    """Get tags that have no children (leaf nodes)."""
    tag_ids_with_children = {tag['parent_tag_id'] for tag in tag_stats if tag['parent_tag_id'] is not None}
    return [tag for tag in tag_stats if tag['id'] not in tag_ids_with_children]


def _get_total_paragraph_count(database: BaseDatabaseInterface) -> int:
    """Get the total number of paragraphs in the database."""
    try:
        stats = database.get_export_statistics()
        return stats.get('total_paragraphs', 0)
    except Exception:
        # Fallback method if get_export_statistics is not available
        return 0


def _calculate_descendant_counts(
    tag_stats: List[Dict], 
    tag_dict: Dict[int, Dict], 
    selected_tag_ids: Set[int]
) -> Dict[int, int]:
    """Calculate the total count including descendants for selected tags only."""
    descendant_counts = {}
    
    def calculate_total_count(tag_id: int) -> int:
        if tag_id in descendant_counts:
            return descendant_counts[tag_id]
        
        tag = tag_dict[tag_id]
        # Only count usage if tag is selected
        total_count = tag['usage_count'] if tag_id in selected_tag_ids else 0
        
        # Add counts from all children (only if they're selected)
        children = [t for t in tag_stats if t['parent_tag_id'] == tag_id]
        for child in children:
            total_count += calculate_total_count(child['id'])
        
        descendant_counts[tag_id] = total_count
        return total_count
    
    # Calculate for all tags
    for tag in tag_stats:
        calculate_total_count(tag['id'])
    
    return descendant_counts


def _render_tag_with_statistics_and_checkbox(
    tag: Dict, 
    tag_dict: Dict[int, Dict], 
    descendant_counts: Dict[int, int],
    total_paragraphs: int,
    selected_tag_ids: Set[int],
    level: int = 0,
    is_last: bool = True,
    parent_prefixes: List[str] = None
) -> None:
    """Render a tag with checkbox, statistics and children recursively."""
    if parent_prefixes is None:
        parent_prefixes = []
    
    # Create tree prefix
    if level == 0:
        prefix = ""
    else:
        prefix_parts = parent_prefixes.copy()
        if is_last:
            prefix_parts.append("└─ ")
        else:
            prefix_parts.append("├─ ")
        prefix = "".join(prefix_parts)
    
    # Get statistics (considering selection)
    direct_count = tag['usage_count'] if tag['id'] in selected_tag_ids else 0
    total_count = descendant_counts.get(tag['id'], direct_count)
    
    # Calculate percentages
    direct_percentage = (direct_count / total_paragraphs * 100) if total_paragraphs > 0 else 0
    total_percentage = (total_count / total_paragraphs * 100) if total_paragraphs > 0 else 0
    
    # Calculate percentage of parent (if applicable)
    parent_percentage = None
    if tag['parent_tag_id'] and tag['parent_tag_id'] in descendant_counts:
        parent_total = descendant_counts[tag['parent_tag_id']]
        if parent_total > 0:
            parent_percentage = (total_count / parent_total * 100)
    
    # Create the display
    checkbox_col, content_col, progress_col = st.columns([0.3, 2.7, 1])
    
    with checkbox_col:
        # Checkbox for tag selection
        is_selected = tag['id'] in selected_tag_ids
        new_selection = st.checkbox(
            "", 
            value=is_selected, 
            key=f"tag_checkbox_{tag['id']}",
            help=f"Include '{tag['name']}' in statistics"
        )
        
        # Update selection if changed
        if new_selection != is_selected:
            if new_selection:
                st.session_state.selected_tags.add(tag['id'])
            else:
                st.session_state.selected_tags.discard(tag['id'])
            st.rerun()
    
    with content_col:
        # Tag name with hierarchy
        if level == 0:
            tag_display = f"🏷️ **{tag['name']}**"
        else:
            tag_display = f"{prefix}🏷️ **{tag['name']}**"
        
        # Add description if available
        if tag.get('description'):
            tag_display += f" - *{tag['description']}*"
        
        # Gray out if not selected
        if not is_selected:
            tag_display = f":gray[{tag_display}]"
        
        st.markdown(tag_display)
        
        # Statistics display (only show if selected or has selected descendants)
        if is_selected or total_count > 0:
            stats_parts = []
            
            # Direct matches
            if direct_count > 0:
                stats_parts.append(f"**Direct:** {direct_count} ({direct_percentage:.1f}%)")
            elif is_selected:
                stats_parts.append("**Direct:** 0")
            
            # Total matches (including descendants)
            if total_count != direct_count and total_count > 0:
                stats_parts.append(f"**Total (incl. descendants):** {total_count} ({total_percentage:.1f}%)")
            
            # Parent percentage
            if parent_percentage is not None and total_count > 0:
                stats_parts.append(f"**Of parent:** {parent_percentage:.1f}%")
            
            if stats_parts:
                # Display statistics with proper indentation
                if level > 0:
                    stats_prefix = prefix.replace("├─", "│ ").replace("└─", "  ")
                else:
                    stats_prefix = "  "
                
                stats_text = " | ".join(stats_parts)
                color = "#666" if is_selected else "#999"
                st.markdown(f"{stats_prefix}<small style='color: {color};'>{stats_text}</small>", 
                           unsafe_allow_html=True)
    
    with progress_col:
        # Progress bar for visualization (only if selected and has counts)
        if is_selected and total_count > 0 and total_paragraphs > 0:
            progress_value = min(total_percentage / 100, 1.0)
            st.progress(progress_value, text=f"{total_percentage:.1f}%")
        elif total_count > 0:
            # Show grayed out progress for unselected tags with selected descendants
            st.markdown(f"<small style='color: #999;'>{total_percentage:.1f}%</small>", 
                       unsafe_allow_html=True)
    
    # Render children
    children = [t for t in tag_dict.values() if t['parent_tag_id'] == tag['id']]
    children.sort(key=lambda x: descendant_counts.get(x['id'], 0), reverse=True)  # Sort by total usage
    
    if children:
        # Update parent prefixes for children
        new_parent_prefixes = parent_prefixes.copy()
        if level >= 0:
            if is_last:
                new_parent_prefixes.append("   ")  # Three spaces for completed branch
            else:
                new_parent_prefixes.append("│  ")  # Vertical line for continuing branch
        
        for j, child in enumerate(children):
            is_last_child = (j == len(children) - 1)
            _render_tag_with_statistics_and_checkbox(
                child, tag_dict, descendant_counts, total_paragraphs, selected_tag_ids,
                level + 1, is_last_child, new_parent_prefixes
            )


def _render_summary_statistics(database: BaseDatabaseInterface) -> None:
    """Render overall summary statistics."""
    try:
        stats = database.get_export_statistics()
        
        st.markdown("### 📈 Summary")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Tags", stats['total_tags'])
            st.metric("Root Tags", stats['root_tags'])
        
        with col2:
            st.metric("Child Tags", stats['child_tags'])
            st.metric("Total Paragraphs", stats['total_paragraphs'])
        
        with col3:
            st.metric("Tagged Paragraphs", stats['tagged_paragraphs'])
            untagged = stats['total_paragraphs'] - stats['tagged_paragraphs']
            st.metric("Untagged Paragraphs", untagged)
        
        with col4:
            if stats['total_paragraphs'] > 0:
                tagged_percentage = (stats['tagged_paragraphs'] / stats['total_paragraphs']) * 100
                st.metric("Tagged %", f"{tagged_percentage:.1f}%")
            else:
                st.metric("Tagged %", "0%")
    
    except Exception as e:
        st.error(f"Could not load summary statistics: {e}")