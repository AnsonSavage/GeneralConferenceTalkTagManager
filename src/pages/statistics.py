"""
Statistics page module - Shows tag tree hierarchy with usage statistics.
"""
import altair as alt
import numpy as np
import pandas as pd
import streamlit as st
from datetime import date, datetime
from typing import Any, Dict, List, Set, Tuple
from ..database.base_database import BaseDatabaseInterface


BASE_COLOR_PALETTE = [
    "#4E79A7",
    "#F28E2B",
    "#E15759",
    "#76B7B2",
    "#59A14F",
    "#EDC948",
    "#B07AA1",
    "#FF9DA7",
    "#9C755F",
    "#BAB0AC",
]


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
    children_map = _build_children_map(tag_stats)
    tag_color_map = _assign_base_colors_to_tags(tag_stats)
    
    # Filter statistics based on selected tags
    filtered_stats = _filter_tag_statistics(tag_stats, st.session_state.selected_tags, database)
    filtered_total_paragraphs = _calculate_filtered_total_paragraphs(
        st.session_state.selected_tags, database
    )
    
    # Calculate descendant counts for filtered tags (both total and unique) - paragraphs
    descendant_counts = _calculate_descendant_counts(filtered_stats, tag_dict, st.session_state.selected_tags)
    unique_descendant_counts = _calculate_unique_descendant_counts(
        filtered_stats, tag_dict, st.session_state.selected_tags, database
    )

    # Calculate talk-based metrics
    talk_counts = _calculate_talk_based_counts(
        filtered_stats, tag_dict, st.session_state.selected_tags, database
    )
    filtered_total_talks = _calculate_filtered_total_talks(
        st.session_state.selected_tags, database
    )
    
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
    
    # Show talk totals
    try:
        export_stats = database.get_export_statistics()
        total_talks_all = export_stats.get('total_talks', 0)
    except Exception:
        total_talks_all = 0
    
    if filtered_total_talks != total_talks_all:
        st.markdown(f"**Total talks (all tags):** {total_talks_all}")
        st.markdown(f"**Total talks (selected tags):** {filtered_total_talks}")
        st.caption("Percentages are calculated based on selected tags only")
    else:
        st.markdown(f"**Total talks in database:** {total_talks_all}")

    histogram_section_rendered = False
    show_histogram = st.checkbox(
        "Show usage histogram over time",
        value=True,
        key="statistics_show_histogram",
        help="Visualize how often the selected tags appear across conferences."
    )
    if show_histogram:
        histogram_section_rendered = True
        st.markdown("### ⏱️ Usage Over Time")
        frequency_options = [6, 12, 18, 24, 30, 36]
        frequency_labels = {
            6: "6 months (per conference)",
            12: "12 months (annual)",
            18: "18 months",
            24: "24 months (biennial)",
            30: "30 months",
            36: "36 months (three years)"
        }
        selected_frequency = st.selectbox(
            "Histogram frequency",
            options=frequency_options,
            index=0,
            format_func=lambda months: frequency_labels.get(months, f"{months} months"),
            help="Group usage counts into bins sized in 6-month increments."
        )

        include_descendants = st.checkbox(
            "Include descendant tags in histogram counts",
            value=st.session_state.get("statistics_include_descendants", True),
            key="statistics_include_descendants",
            help="When enabled, each tag's histogram sums paragraphs from its subcategories."
        )
        include_descendants = st.session_state.statistics_include_descendants

        histogram_tag_ids = (
            _expand_tags_with_descendants(st.session_state.selected_tags, children_map)
            if include_descendants else set(st.session_state.selected_tags)
        )

        time_series_data = database.get_tag_usage_time_series(histogram_tag_ids)
        per_tag_time_series = database.get_tag_usage_time_series(
            histogram_tag_ids,
            by_tag=True
        )
        per_tag_series_map: Dict[int, List[Dict[str, Any]]] = {}
        for entry in per_tag_time_series:
            tag_id = entry.get('tag_id')
            if tag_id is None:
                continue
            per_tag_series_map.setdefault(tag_id, []).append({
                'conference_date': entry.get('conference_date'),
                'paragraph_count': entry.get('paragraph_count', 0)
            })
        for series in per_tag_series_map.values():
            series.sort(key=lambda item: item.get('conference_date') or '')

        per_tag_histogram_inputs: Dict[int, List[Dict[str, Any]]] = {}
        for tag_id in st.session_state.selected_tags:
            relevant_ids = {tag_id}
            if include_descendants:
                relevant_ids.update(_get_descendant_ids(tag_id, children_map))
            per_tag_histogram_inputs[tag_id] = _combine_time_series_for_tags(
                per_tag_series_map,
                relevant_ids
            )

        histogram_data = _build_usage_histogram(time_series_data, selected_frequency)

        if histogram_data:
            df, slope, intercept, r_squared = _prepare_histogram_dataframe(histogram_data)
            if not df.empty:
                chart = _create_usage_histogram_chart(df)
                st.altair_chart(chart, use_container_width=True)
                st.caption(
                    f"Line of best fit (per {selected_frequency}-month bin): y = {slope:.2f}x + {intercept:.2f}; R² = {r_squared:.3f}"
                )
            else:
                st.info("Not enough data to render the histogram.")
        else:
            st.info("No usage data available for the selected tags.")

        if per_tag_histogram_inputs:
            st.markdown("#### Individual Tag Trends")
            for tag_id in sorted(
                st.session_state.selected_tags,
                key=lambda tid: tag_dict.get(tid, {}).get('name', '')
            ):
                tag = tag_dict.get(tag_id)
                series = per_tag_histogram_inputs.get(tag_id, [])
                if not tag or not series:
                    continue

                tag_histogram_data = _build_usage_histogram(series, selected_frequency)
                if not tag_histogram_data:
                    continue

                tag_df, tag_slope, tag_intercept, tag_r_squared = _prepare_histogram_dataframe(tag_histogram_data)
                if tag_df.empty:
                    continue

                st.markdown(f"**{tag['name']}**")
                tag_chart = _create_usage_histogram_chart(tag_df)
                st.altair_chart(tag_chart, use_container_width=True)
                st.caption(
                    f"Trend: y = {tag_slope:.2f}x + {tag_intercept:.2f}; R² = {tag_r_squared:.3f}"
                )
    
    composition_section_rendered = False
    candidate_parents: List[Tuple[Dict[str, Any], List[int]]] = []
    for tag in tag_stats:
        child_ids = [
            child_id for child_id in children_map.get(tag['id'], [])
            if child_id in st.session_state.selected_tags
        ]
        if tag['id'] in st.session_state.selected_tags and child_ids:
            candidate_parents.append((tag, child_ids))

    if candidate_parents:
        st.divider()
        st.markdown("### 🥧 Category Composition (Immediate Children)")
        filter_text = st.text_input(
            "Show pie charts for categories containing (optional)",
            key="statistics_composition_filter",
            help=(
                "Type part of a category name (comma-separated for multiple) to display its "
                "subcategories' composition. Leave blank to show all matching categories."
            ),
        ).strip()
        filter_terms = {
            term.strip().lower() for term in filter_text.split(",") if term.strip()
        }

        paragraph_cache: Dict[int, Set[int]] = {}
        charts_rendered = 0
        row_columns: Tuple[Any, Any] = (None, None)
        for tag, child_ids in candidate_parents:
            if filter_terms:
                name_lower = tag['name'].lower()
                if not any(term in name_lower for term in filter_terms):
                    continue

            segments, total_count = _calculate_category_composition_segments(
                child_tag_ids=child_ids,
                database=database,
                paragraph_cache=paragraph_cache,
                tag_dict=tag_dict,
                base_color_map=tag_color_map,
            )
            if not segments:
                continue

            if charts_rendered % 2 == 0:
                row_columns = st.columns(2)
            target_column = row_columns[charts_rendered % 2]
            with target_column:
                chart = _create_category_composition_chart(segments, title=tag['name'])
                st.altair_chart(chart, use_container_width=True)
                st.caption(
                    f"{total_count} paragraphs across {len(child_ids)} subcategories"
                )
            charts_rendered += 1

        if charts_rendered == 0:
            st.info("No matching categories with overlapping subcategory usage found.")
        else:
            composition_section_rendered = True

    if filtered_total_paragraphs > 0 or filtered_total_talks > 0:
        if composition_section_rendered or not histogram_section_rendered:
            st.divider()
        
        # Render each root tag and its hierarchy with checkboxes
        for i, root_tag in enumerate(root_tags):
            _render_tag_with_statistics_and_checkbox(
                root_tag, tag_dict,
                descendant_counts, unique_descendant_counts, filtered_total_paragraphs,
                st.session_state.selected_tags,
                talk_counts['direct_talk_counts'],
                talk_counts['total_talk_descendant_counts'],
                talk_counts['unique_talk_descendant_counts'],
                filtered_total_talks,
                level=0
            )
            if i < len(root_tags) - 1:
                st.divider()
    else:
        st.warning("No paragraphs or talks found for the selected tags.")


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


def _calculate_filtered_total_talks(selected_tag_ids: Set[int], database: BaseDatabaseInterface) -> int:
    """Calculate total unique talks that have any of the selected tags (via paragraphs)."""
    if not selected_tag_ids:
        return 0
    unique_talk_ids = set()
    for tag_id in selected_tag_ids:
        paragraphs = database.get_paragraphs_by_tag(tag_id)
        unique_talk_ids.update(p['talk_id'] for p in paragraphs)
    return len(unique_talk_ids)


def _get_leaf_tags(tag_stats: List[Dict]) -> List[Dict]:
    """Get tags that have no children (leaf nodes)."""
    tag_ids_with_children = {tag['parent_tag_id'] for tag in tag_stats if tag['parent_tag_id'] is not None}
    return [tag for tag in tag_stats if tag['id'] not in tag_ids_with_children]


def _build_children_map(tag_stats: List[Dict]) -> Dict[int, List[int]]:
    """Build a mapping of parent tag IDs to their child tag IDs."""
    children_map: Dict[int, List[int]] = {}
    for tag in tag_stats:
        parent_id = tag.get('parent_tag_id')
        if parent_id is not None:
            children_map.setdefault(parent_id, []).append(tag['id'])
    return children_map


def _get_descendant_ids(tag_id: int, children_map: Dict[int, List[int]]) -> Set[int]:
    """Return all descendant tag IDs for a given tag (excluding the tag itself)."""
    descendants: Set[int] = set()
    stack = list(children_map.get(tag_id, []))
    while stack:
        current = stack.pop()
        if current in descendants:
            continue
        descendants.add(current)
        stack.extend(children_map.get(current, []))
    return descendants


def _expand_tags_with_descendants(selected_tag_ids: Set[int], children_map: Dict[int, List[int]]) -> Set[int]:
    """Expand a tag selection to include all descendant tags."""
    expanded: Set[int] = set()
    for tag_id in selected_tag_ids:
        expanded.add(tag_id)
        expanded.update(_get_descendant_ids(tag_id, children_map))
    return expanded


def _combine_time_series_for_tags(
    series_map: Dict[int, List[Dict[str, Any]]],
    tag_ids: Set[int]
) -> List[Dict[str, Any]]:
    """Aggregate multiple tag time series into a single time series."""
    aggregated_counts: Dict[str, int] = {}
    for tag_id in tag_ids:
        for entry in series_map.get(tag_id, []):
            date_key = entry.get('conference_date')
            if not date_key:
                continue
            count_value = int(entry.get('paragraph_count', 0) or 0)
            aggregated_counts[date_key] = aggregated_counts.get(date_key, 0) + count_value

    if not aggregated_counts:
        return []

    return [
        {'conference_date': date_key, 'paragraph_count': aggregated_counts[date_key]}
        for date_key in sorted(aggregated_counts.keys())
    ]


def _assign_base_colors_to_tags(tag_stats: List[Dict[str, Any]]) -> Dict[int, str]:
    """Assign a consistent base color to each tag for visualization."""
    color_map: Dict[int, str] = {}
    for index, tag in enumerate(sorted(tag_stats, key=lambda item: item['id'])):
        color_map[tag['id']] = BASE_COLOR_PALETTE[index % len(BASE_COLOR_PALETTE)]
    return color_map


def _get_paragraph_ids_for_tag(
    tag_id: int,
    database: BaseDatabaseInterface,
    paragraph_cache: Dict[int, Set[int]]
) -> Set[int]:
    """Fetch and cache paragraph IDs for a tag."""
    if tag_id not in paragraph_cache:
        paragraphs = database.get_paragraphs_by_tag(tag_id)
        paragraph_cache[tag_id] = {p['id'] for p in paragraphs}
    return paragraph_cache[tag_id]


def _hex_to_rgb(color: str) -> Tuple[int, int, int]:
    """Convert a hex color string to an RGB tuple."""
    hex_color = color.lstrip('#')
    if len(hex_color) != 6:
        return (128, 128, 128)
    return tuple(int(hex_color[i:i + 2], 16) for i in (0, 2, 4))


def _blend_segment_color(
    combo_tag_ids: Tuple[int, ...],
    base_color_map: Dict[int, str]
) -> str:
    """Blend base colors for a combination of tags."""
    rgb_values = [_hex_to_rgb(base_color_map.get(tag_id, BASE_COLOR_PALETTE[0])) for tag_id in combo_tag_ids]
    count = max(1, len(rgb_values))
    averaged = tuple(
        int(round(sum(value[channel] for value in rgb_values) / count))
        for channel in range(3)
    )
    alpha = 0.55 if count == 1 else min(1.0, 0.55 + 0.15 * (count - 1))
    return f"rgba({averaged[0]}, {averaged[1]}, {averaged[2]}, {alpha:.2f})"


def _calculate_category_composition_segments(
    child_tag_ids: List[int],
    database: BaseDatabaseInterface,
    paragraph_cache: Dict[int, Set[int]],
    tag_dict: Dict[int, Dict[str, Any]],
    base_color_map: Dict[int, str]
) -> Tuple[List[Dict[str, Any]], int]:
    """Calculate paragraph distribution among immediate child combinations."""
    if not child_tag_ids:
        return [], 0

    paragraph_to_children: Dict[int, Set[int]] = {}
    for child_id in child_tag_ids:
        for paragraph_id in _get_paragraph_ids_for_tag(child_id, database, paragraph_cache):
            paragraph_to_children.setdefault(paragraph_id, set()).add(child_id)

    combo_counts: Dict[Tuple[int, ...], int] = {}
    for combo in paragraph_to_children.values():
        if not combo:
            continue
        combo_key = tuple(sorted(combo))
        combo_counts[combo_key] = combo_counts.get(combo_key, 0) + 1

    if not combo_counts:
        return [], 0

    total_count = sum(combo_counts.values())
    segments: List[Dict[str, Any]] = []
    sorted_combos = sorted(
        combo_counts.items(),
        key=lambda item: (
            -item[1],
            len(item[0]),
            tuple(tag_dict[tag_id]['name'].lower() for tag_id in item[0])
        )
    )

    for combo_key, count in sorted_combos:
        child_names = [tag_dict[tag_id]['name'] for tag_id in combo_key]
        label = " + ".join(child_names)
        segments.append({
            'segment_label': label,
            'paragraph_count': count,
            'percentage': (count / total_count) * 100,
            'color': _blend_segment_color(combo_key, base_color_map),
            'combo_key': "|".join(str(tag_id) for tag_id in combo_key),
            'subcategory_count': len(combo_key),
        })

    return segments, total_count


def _create_category_composition_chart(
    segments: List[Dict[str, Any]],
    title: str
) -> alt.Chart:
    """Create a pie chart visualizing category composition segments."""
    if not segments:
        return alt.Chart(pd.DataFrame({'segment_label': [], 'paragraph_count': []}))

    df = pd.DataFrame(segments)
    color_domain = df['segment_label'].tolist()
    color_range = df['color'].tolist()

    base = alt.Chart(df).encode(
        theta=alt.Theta('paragraph_count:Q', stack=True),
        color=alt.Color(
            'segment_label:N',
            scale=alt.Scale(domain=color_domain, range=color_range),
            legend=alt.Legend(title='Combination')
        ),
        order=alt.Order('paragraph_count:Q', sort='descending')
    )

    pie = base.mark_arc(innerRadius=40, outerRadius=140).encode(
        tooltip=[
            alt.Tooltip('segment_label:N', title='Combination'),
            alt.Tooltip('paragraph_count:Q', title='Paragraphs'),
            alt.Tooltip('percentage:Q', title='Percentage', format='.1f')
        ]
    )

    labels = alt.Chart(df).mark_text(radius=120, fill='#333', fontWeight='bold').encode(
        theta=alt.Theta('paragraph_count:Q', stack=True),
        text=alt.Text('percentage:Q', format='.1f')
    )

    return (pie + labels).properties(width=360, height=360, title=title)


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


def _calculate_unique_descendant_counts(
    tag_stats: List[Dict], 
    tag_dict: Dict[int, Dict], 
    selected_tag_ids: Set[int],
    database: BaseDatabaseInterface
) -> Dict[int, int]:
    """Calculate the unique paragraph count including descendants for selected tags only."""
    unique_descendant_counts = {}
    
    def get_unique_paragraphs_for_tag_and_descendants(tag_id: int) -> Set[int]:
        """Get unique paragraph IDs for a tag and all its descendants."""
        # Build the set recursively
        unique_paragraph_ids = set()
        
        # Add paragraphs from this tag if it's selected
        if tag_id in selected_tag_ids:
            paragraphs = database.get_paragraphs_by_tag(tag_id)
            unique_paragraph_ids.update(p['id'] for p in paragraphs)
        
        # Add paragraphs from all children (only if they're selected)
        children = [t for t in tag_stats if t['parent_tag_id'] == tag_id]
        for child in children:
            child_paragraph_ids = get_unique_paragraphs_for_tag_and_descendants(child['id'])
            unique_paragraph_ids.update(child_paragraph_ids)
        
        return unique_paragraph_ids
    
    # Calculate unique counts for all tags
    for tag in tag_stats:
        unique_paragraph_ids = get_unique_paragraphs_for_tag_and_descendants(tag['id'])
        unique_descendant_counts[tag['id']] = len(unique_paragraph_ids)
    
    return unique_descendant_counts


def _calculate_talk_based_counts(
    tag_stats: List[Dict],
    tag_dict: Dict[int, Dict],
    selected_tag_ids: Set[int],
    database: BaseDatabaseInterface
) -> Dict[str, Dict[int, int]]:
    """Calculate direct, total (non-unique), and unique talk counts including descendants."""
    direct_talk_counts: Dict[int, int] = {}
    total_talk_descendant_counts: Dict[int, int] = {}
    unique_talk_descendant_counts: Dict[int, int] = {}

    # Cache talk sets per tag to avoid duplicate DB calls
    talk_set_cache: Dict[int, Set[int]] = {}

    def get_direct_talk_set(tag_id: int) -> Set[int]:
        if tag_id in talk_set_cache:
            return talk_set_cache[tag_id]
        talks = set()
        if tag_id in selected_tag_ids:
            paragraphs = database.get_paragraphs_by_tag(tag_id)
            talks.update(p['talk_id'] for p in paragraphs)
        talk_set_cache[tag_id] = talks
        return talks

    def compute_totals(tag_id: int) -> None:
        # Direct talks
        direct_set = get_direct_talk_set(tag_id)
        direct_talk_counts[tag_id] = len(direct_set)
        
        # Sum totals from children (non-unique)
        children = [t for t in tag_stats if t['parent_tag_id'] == tag_id]
        child_total_sum = 0
        child_unique_set: Set[int] = set()
        for child in children:
            compute_totals(child['id'])
            child_total_sum += total_talk_descendant_counts[child['id']]
            child_unique_set.update(_get_unique_talk_set(child['id']))
        
        total_talk_descendant_counts[tag_id] = (len(direct_set) if tag_id in selected_tag_ids else 0) + child_total_sum
        unique_talk_descendant_counts[tag_id] = len((direct_set if tag_id in selected_tag_ids else set()) | child_unique_set)

    # Helper to build unique set for a tag and descendants
    unique_talk_set_cache: Dict[int, Set[int]] = {}
    def _get_unique_talk_set(tag_id: int) -> Set[int]:
        if tag_id in unique_talk_set_cache:
            return unique_talk_set_cache[tag_id]
        unique_set = set(get_direct_talk_set(tag_id)) if tag_id in selected_tag_ids else set()
        for child in [t for t in tag_stats if t['parent_tag_id'] == tag_id]:
            unique_set.update(_get_unique_talk_set(child['id']))
        unique_talk_set_cache[tag_id] = unique_set
        return unique_set

    # Compute for all tags
    for tag in tag_stats:
        if tag['id'] not in direct_talk_counts:
            compute_totals(tag['id'])

    return {
        'direct_talk_counts': direct_talk_counts,
        'total_talk_descendant_counts': total_talk_descendant_counts,
        'unique_talk_descendant_counts': unique_talk_descendant_counts,
    }


def _build_usage_histogram(
    time_series_data: List[Dict[str, Any]],
    frequency_months: int
) -> List[Dict[str, Any]]:
    """Convert raw time series data into aggregated histogram bins."""
    if not time_series_data or frequency_months <= 0:
        return []

    parsed_entries: List[Tuple[date, int]] = []
    for entry in time_series_data:
        raw_date = entry.get('conference_date')
        if not raw_date:
            continue
        try:
            period_date = datetime.fromisoformat(raw_date).date()
        except ValueError:
            continue
        count_value = int(entry.get('paragraph_count', 0) or 0)
        parsed_entries.append((period_date, count_value))

    if not parsed_entries:
        return []

    parsed_entries.sort(key=lambda item: item[0])
    bin_size = max(1, frequency_months // 6)

    histogram: List[Dict[str, Any]] = []
    index = 0
    total_entries = len(parsed_entries)
    while index < total_entries:
        bin_slice = parsed_entries[index:index + bin_size]
        if not bin_slice:
            break
        period_start = bin_slice[0][0]
        period_end = bin_slice[-1][0]
        paragraph_sum = sum(value for _, value in bin_slice)
        histogram.append({
            'period_start': period_start,
            'period_end': period_end,
            'label': _format_period_label(period_start, period_end),
            'paragraph_count': paragraph_sum
        })
        index += bin_size

    return histogram


def _prepare_histogram_dataframe(
    histogram_data: List[Dict[str, Any]]
) -> Tuple[pd.DataFrame, float, float, float]:
    """Build a dataframe and regression metrics for the usage histogram."""
    if not histogram_data:
        return pd.DataFrame(), 0.0, 0.0, 0.0

    df = pd.DataFrame(histogram_data)
    df['period_start'] = pd.to_datetime(df['period_start'])
    df['period_end'] = pd.to_datetime(df['period_end'])
    df['index'] = np.arange(len(df), dtype=float)

    y_values = df['paragraph_count'].astype(float).to_numpy()
    x_values = df['index'].to_numpy()

    if len(df) >= 2:
        slope, intercept = np.polyfit(x_values, y_values, 1)
        trend = slope * x_values + intercept
    elif len(df) == 1:
        slope = 0.0
        intercept = float(y_values[0])
        trend = np.full_like(x_values, intercept)
    else:
        return pd.DataFrame(), 0.0, 0.0, 0.0

    if len(y_values) > 0:
        ss_res = np.sum((y_values - trend) ** 2)
        ss_tot = np.sum((y_values - np.mean(y_values)) ** 2)
        r_squared = 1 - ss_res / ss_tot if ss_tot > 0 else 1.0
    else:
        r_squared = 0.0

    df['trend'] = trend
    return df, float(slope), float(intercept), float(r_squared)


def _create_usage_histogram_chart(df: pd.DataFrame) -> alt.Chart:
    """Create an Altair chart combining histogram bars with a trend line."""
    base = alt.Chart(df).encode(
        x=alt.X(
            'period_start:T',
            title='Conference period',
            axis=alt.Axis(format='%Y', labelAngle=0)
        )
    )

    bars = base.mark_bar(color='#4E79A7').encode(
        y=alt.Y('paragraph_count:Q', title='Paragraph count'),
        tooltip=[
            alt.Tooltip('label:N', title='Period'),
            alt.Tooltip('paragraph_count:Q', title='Paragraph count')
        ]
    )

    trend_line = base.mark_line(color='#F28E2B', strokeWidth=2).encode(
        y=alt.Y('trend:Q', title='Trend estimate')
    )

    trend_points = base.mark_point(color='#F28E2B', filled=True).encode(
        y='trend:Q',
        tooltip=[
            alt.Tooltip('label:N', title='Period'),
            alt.Tooltip('trend:Q', title='Trend estimate', format='.2f')
        ]
    )

    return (bars + trend_line + trend_points).properties(height=360)


def _format_period_label(start: date, end: date) -> str:
    """Format a readable label for a histogram period."""
    if start == end:
        return start.strftime('%b %Y')
    return f"{start.strftime('%b %Y')} - {end.strftime('%b %Y')}"


def _render_tag_with_statistics_and_checkbox(
    tag: Dict, 
    tag_dict: Dict[int, Dict], 
    descendant_counts: Dict[int, int],
    unique_descendant_counts: Dict[int, int],
    total_paragraphs: int,
    selected_tag_ids: Set[int],
    direct_talk_counts: Dict[int, int],
    total_talk_descendant_counts: Dict[int, int],
    unique_talk_descendant_counts: Dict[int, int],
    total_talks: int,
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
    
    # Get paragraph statistics (considering selection)
    direct_count = tag['usage_count'] if tag['id'] in selected_tag_ids else 0
    total_count = descendant_counts.get(tag['id'], direct_count)
    unique_count = unique_descendant_counts.get(tag['id'], direct_count)

    # Get talk statistics (considering selection)
    direct_talks = direct_talk_counts.get(tag['id'], 0) if tag['id'] in selected_tag_ids else 0
    total_talks_count = total_talk_descendant_counts.get(tag['id'], direct_talks)
    unique_talks_count = unique_talk_descendant_counts.get(tag['id'], direct_talks)
    
    # Calculate percentages (paragraph-based)
    direct_percentage = (direct_count / total_paragraphs * 100) if total_paragraphs > 0 else 0
    total_percentage = (total_count / total_paragraphs * 100) if total_paragraphs > 0 else 0
    unique_percentage = (unique_count / total_paragraphs * 100) if total_paragraphs > 0 else 0

    # Calculate percentages (talk-based)
    direct_talks_pct = (direct_talks / total_talks * 100) if total_talks > 0 else 0
    total_talks_pct = (total_talks_count / total_talks * 100) if total_talks > 0 else 0
    unique_talks_pct = (unique_talks_count / total_talks * 100) if total_talks > 0 else 0
    
    # Calculate percentage of parent (paragraphs) if applicable
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
        if is_selected or total_count > 0 or total_talks_count > 0:
            stats_parts = []
            
            # Paragraph stats
            if direct_count > 0 or is_selected:
                stats_parts.append(f"**Direct paragraphs:** {direct_count} ({direct_percentage:.1f}%)")
            if total_count != direct_count and total_count > 0:
                stats_parts.append(f"**Total paragraphs (incl. descendants):** {total_count} ({total_percentage:.1f}%)")
            if unique_count != total_count and unique_count > 0:
                stats_parts.append(f"**Unique paragraphs (incl. descendants):** {unique_count} ({unique_percentage:.1f}%)")
            
            # Talk stats
            if direct_talks > 0 or is_selected:
                stats_parts.append(f"**Direct talks:** {direct_talks} ({direct_talks_pct:.1f}%)")
            if total_talks_count != direct_talks and total_talks_count > 0:
                stats_parts.append(f"**Total talks (incl. descendants):** {total_talks_count} ({total_talks_pct:.1f}%)")
            if unique_talks_count != total_talks_count and unique_talks_count > 0:
                stats_parts.append(f"**Unique talks (incl. descendants):** {unique_talks_count} ({unique_talks_pct:.1f}%)")
            
            # Parent percentage (paragraph-based)
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
        # Progress bar for visualization (use unique paragraphs by default)
        if is_selected and unique_count > 0 and total_paragraphs > 0:
            progress_value = min(unique_percentage / 100, 1.0)
            st.progress(progress_value, text=f"{unique_percentage:.1f}% para")
        elif unique_count > 0:
            st.markdown(f"<small style='color: #999;'>{unique_percentage:.1f}% para</small>", 
                       unsafe_allow_html=True)
        # Also show talks percentage as text for quick reference
        if unique_talks_count > 0 and total_talks > 0:
            st.markdown(f"<small style='color: #666;'>{unique_talks_pct:.1f}% talks</small>", 
                        unsafe_allow_html=True)
    
    # Render children
    children = [t for t in tag_dict.values() if t['parent_tag_id'] == tag['id']]
    children.sort(key=lambda x: unique_descendant_counts.get(x['id'], 0), reverse=True)  # Sort by unique usage
    
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
                child, tag_dict, descendant_counts, unique_descendant_counts, total_paragraphs, 
                selected_tag_ids, direct_talk_counts, total_talk_descendant_counts, unique_talk_descendant_counts, 
                total_talks, level + 1, is_last_child, new_parent_prefixes
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
        
        # Additional talk-level summary
        col5, col6 = st.columns(2)
        with col5:
            st.metric("Total Talks", stats.get('total_talks', 0))
        with col6:
            tagged_talks = stats.get('tagged_talks', 0)
            total_talks = stats.get('total_talks', 0)
            pct = (tagged_talks / total_talks * 100) if total_talks else 0
            st.metric("Tagged Talks", f"{tagged_talks} ({pct:.1f}%)")
    
    except Exception as e:
        st.error(f"Could not load summary statistics: {e}")