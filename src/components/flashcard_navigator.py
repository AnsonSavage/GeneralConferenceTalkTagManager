"""
Flashcard navigation component for the Conference Talks Analysis application.
"""
import streamlit as st
from typing import List, Any, Optional
from streamlit_shortcuts import shortcut_button, add_shortcuts
from ..utils.helpers import get_random_index


class FlashcardNavigator:
    """Component for navigating through items in a flashcard-style interface."""
    
    def __init__(self, items: List[Any], session_key: str = "current_index"):
        self.items = items
        self.session_key = session_key
        self.total_items = len(items)
        
    def get_current_index(self) -> int:
        """Get the current index from session state."""
        if self.session_key not in st.session_state:
            st.session_state[self.session_key] = 0
        
        # Ensure index is within bounds
        if st.session_state[self.session_key] >= self.total_items:
            st.session_state[self.session_key] = 0
            
        return st.session_state[self.session_key]
    
    def get_current_item(self) -> Any:
        """Get the current item based on the index."""
        if not self.items:
            return None
        return self.items[self.get_current_index()]
    
    def move_to_next(self) -> bool:
        """Move to the next item. Returns True if moved, False if already at end."""
        current_index = self.get_current_index()
        if current_index < self.total_items - 1:
            st.session_state[self.session_key] = current_index + 1
            return True
        return False
    
    def move_to_previous(self) -> bool:
        """Move to the previous item. Returns True if moved, False if already at start."""
        current_index = self.get_current_index()
        if current_index > 0:
            st.session_state[self.session_key] = current_index - 1
            return True
        return False
    
    def get_next_unreviewed_index(self, current_index: int) -> Optional[int]:
        """Find the next unreviewed item index starting from current_index + 1."""
        # Search forward from current position
        for i in range(current_index + 1, self.total_items):
            if not self.items[i].get('reviewed', False):
                return i
        
        # If no unreviewed items found after current position, search from beginning
        for i in range(0, current_index):
            if not self.items[i].get('reviewed', False):
                return i
        
        # No unreviewed items found
        return None
    
    def get_previous_unreviewed_index(self, current_index: int) -> Optional[int]:
        """Find the previous unreviewed item index starting from current_index - 1."""
        # Search backward from current position
        for i in range(current_index - 1, -1, -1):
            if not self.items[i].get('reviewed', False):
                return i
        
        # If no unreviewed items found before current position, search from end
        for i in range(self.total_items - 1, current_index, -1):
            if not self.items[i].get('reviewed', False):
                return i
        
        # No unreviewed items found
        return None

    def get_reviewed_count(self) -> int:
        """Get the count of reviewed items."""
        return sum(1 for item in self.items if item.get('reviewed', False))
    
    def render_simple_navigation(self) -> None:
        """Render simple navigation controls without auto-completion logic."""
        if not self.items:
            return
            
        current_index = self.get_current_index()
        reviewed_count = self.get_reviewed_count()
        
        # Progress bar showing overall progress
        progress = (current_index + 1) / self.total_items if self.total_items > 0 else 0
        st.progress(progress, text=f"Card {current_index + 1} of {self.total_items} • {reviewed_count} reviewed")
        
        # Navigation controls
        col1, col2, col3, col4 = st.columns([1, 1, 2, 1])
        
        with col1:
            if st.button("⬅️ Previous", disabled=current_index == 0, key=f"simple_prev_{self.session_key}"):
                self.move_to_previous()
                st.rerun()
        
        with col2:
            if st.button("➡️ Next", disabled=current_index == self.total_items - 1, key=f"simple_next_{self.session_key}"):
                self.move_to_next()
                st.rerun()
        
        with col3:
            st.write(f"**Card {current_index + 1} of {self.total_items}**")
        
        with col4:
            if st.button("🔄 Random", key=f"simple_random_{self.session_key}"):
                st.session_state[self.session_key] = get_random_index(self.total_items)
                st.rerun()

    def render_navigation(self) -> None:
        """Render the navigation controls."""
        if not self.items:
            return
            
        current_index = self.get_current_index()
        
        col1, col2, col3, col4, col5 = st.columns([1, 1, 2, 1, 1])
        
        with col1:
            if st.button("⬅️ Previous", disabled=current_index == 0):
                st.session_state[self.session_key] = current_index - 1
                st.rerun()
        
        with col2:
            if st.button("➡️ Next", disabled=current_index == self.total_items - 1):
                st.session_state[self.session_key] = current_index + 1
                st.rerun()
        
        with col3:
            st.write(f"**Item {current_index + 1} of {self.total_items}**")
        
        with col4:
            if st.button("🔄 Random"):
                st.session_state[self.session_key] = get_random_index(self.total_items)
                st.rerun()
        
        with col5:
            jump_to = st.number_input(
                "Jump to:", 
                min_value=1, 
                max_value=self.total_items,
                value=current_index + 1, 
                key=f"jump_input_{self.session_key}"
            )
            if st.button("Go", key=f"go_button_{self.session_key}"):
                st.session_state[self.session_key] = jump_to - 1
                st.rerun()

    def render_enhanced_navigation(self) -> None:
        """Render enhanced navigation controls with progress tracking and review functionality."""
        if not self.items:
            return
            
        current_index = self.get_current_index()
        reviewed_count = self.get_reviewed_count()
        
        # Progress tracking for reviewed items
        review_progress = reviewed_count / self.total_items if self.total_items > 0 else 0
        
        # Display review progress bar
        st.markdown("**Review Progress:**")
        st.progress(review_progress, text=f"Reviewed {reviewed_count} of {self.total_items} paragraphs ({review_progress:.1%})")
        
        # Current item position
        st.markdown(f"**Current:** Paragraph {current_index + 1} of {self.total_items}")
        
        # Navigation buttons
        col1, col2, col3, col4, col5, col6 = st.columns([1, 1, 1, 1, 1, 2])
        
        with col1:
            if st.button(
                "⬅️ Previous", 
                disabled=current_index == 0,
                help="Previous paragraph (Left Arrow)",
                key=f"prev_{self.session_key}"
            ):
                st.session_state[self.session_key] = current_index - 1
                st.rerun()
        
        with col2:
            if st.button(
                "➡️ Next", 
                disabled=current_index == self.total_items - 1,
                help="Next paragraph (Right Arrow)",
                key=f"next_{self.session_key}"
            ):
                st.session_state[self.session_key] = current_index + 1
                st.rerun()
        
        with col3:
            # Next unreviewed button
            next_unreviewed_idx = self.get_next_unreviewed_index(current_index)
            if st.button(
                "⏭️ Next Unreviewed",
                disabled=next_unreviewed_idx is None,
                help="Jump to next unreviewed paragraph",
                key=f"next_unreviewed_{self.session_key}"
            ):
                if next_unreviewed_idx is not None:
                    st.session_state[self.session_key] = next_unreviewed_idx
                    st.rerun()
        
        with col4:
            if st.button(
                "🔄 Random",
                help="Random paragraph (R key)",
                key=f"random_{self.session_key}"
            ):
                st.session_state[self.session_key] = get_random_index(self.total_items)
                st.rerun()
        
        with col5:
            if st.button(
                "⏮️ First",
                help="Go to first paragraph",
                key=f"first_{self.session_key}"
            ):
                st.session_state[self.session_key] = 0
                st.rerun()
        
        with col6:
            # Quick jump input
            jump_col1, jump_col2 = st.columns([2, 1])
            with jump_col1:
                jump_to = st.number_input(
                    "Jump to:", 
                    min_value=1, 
                    max_value=self.total_items,
                    value=current_index + 1, 
                    key=f"jump_input_enhanced_{self.session_key}",
                    help="Enter a number to jump to that paragraph"
                )
            with jump_col2:
                if st.button("Go", key=f"go_button_enhanced_{self.session_key}"):
                    st.session_state[self.session_key] = jump_to - 1
                    st.rerun()

    def render_floating_navigation(self) -> None:
        """Render floating navigation controls at the bottom of the page."""
        if not self.items:
            return
            
        current_index = self.get_current_index()
        
        # Create floating navigation container
        st.markdown("""
        <style>
        .floating-nav {
            position: fixed;
            bottom: 20px;
            left: 50%;
            transform: translateX(-50%);
            background: rgba(28, 131, 225, 0.95);
            backdrop-filter: blur(10px);
            border-radius: 50px;
            padding: 15px 25px;
            box-shadow: 0 8px 32px rgba(0,0,0,0.3);
            z-index: 1000;
            display: flex;
            align-items: center;
            gap: 15px;
            color: white;
            font-weight: bold;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # Progress and navigation in columns
        col1, col2, col3, col4, col5 = st.columns([1, 1, 2, 1, 1])
        
        with col1:
            if st.button("⬅️", disabled=current_index == 0, key=f"floating_prev_{self.session_key}", help="Previous"):
                st.session_state[self.session_key] = current_index - 1
                st.rerun()
        
        with col2:
            if st.button("➡️", disabled=current_index == self.total_items - 1, key=f"floating_next_{self.session_key}", help="Next"):
                st.session_state[self.session_key] = current_index + 1
                st.rerun()
        
        with col3:
            progress = (current_index + 1) / self.total_items
            st.progress(progress, text=f"{current_index + 1} of {self.total_items}")
        
        with col4:
            if st.button("🔄", key=f"floating_random_{self.session_key}", help="Random"):
                st.session_state[self.session_key] = get_random_index(self.total_items)
                st.rerun()
        
        with col5:
            if st.button("⏭️", key=f"floating_first_{self.session_key}", help="First"):
                st.session_state[self.session_key] = 0
                st.rerun()
    
    def mark_current_reviewed_and_move_to_next_unreviewed(self, database) -> bool:
        """
        Mark current item as reviewed and automatically move to next unreviewed item.
        
        Args:
            database: Database instance to mark the paragraph as reviewed
            
        Returns:
            True if successfully moved to next unreviewed item, False if no more unreviewed items
        """
        current_index = self.get_current_index()
        current_item = self.get_current_item()
        
        if current_item and 'id' in current_item:
            # Mark current paragraph as reviewed
            database.mark_paragraph_reviewed(current_item['id'], True)
            
            # Update the item in our local list
            self.items[current_index]['reviewed'] = True
            
            # Find next unreviewed item
            next_unreviewed_idx = self.get_next_unreviewed_index(current_index)
            
            if next_unreviewed_idx is not None:
                st.session_state[self.session_key] = next_unreviewed_idx
                return True
            else:
                # No more unreviewed items, stay at current position
                return False
        
        return False
    
    def mark_current_reviewed_and_move_to_next(self, database) -> bool:
        """
        Mark current item as reviewed and move to next item (regardless of review status).
        
        Args:
            database: Database instance to mark the paragraph as reviewed
            
        Returns:
            True if successfully moved to next item, False if no more items
        """
        current_index = self.get_current_index()
        current_item = self.get_current_item()
        
        if current_item and 'id' in current_item:
            # Mark current paragraph as reviewed
            database.mark_paragraph_reviewed(current_item['id'], True)
            
            # Update the item in our local list
            self.items[current_index]['reviewed'] = True
            
            # Move to next item
            return self.move_to_next()
        
        return False
    
    def render_dual_navigation(self) -> None:
        """Render dual navigation system with both sequential and unreviewed-only navigation."""
        if not self.items:
            return
            
        current_index = self.get_current_index()
        reviewed_count = self.get_reviewed_count()
        
        # Overall progress
        progress = reviewed_count / self.total_items if self.total_items > 0 else 0
        st.progress(progress, text=f"Reviewed {reviewed_count} of {self.total_items} paragraphs ({progress:.1%})")
        
        # Current position indicator
        st.markdown(f"**Current Position:** Paragraph {current_index + 1} of {self.total_items}")
        
        st.markdown("---")
        
        # Dual navigation system with keyboard shortcuts
        st.markdown("### 🧭 Navigation Controls")
        
        # Sequential navigation row
        st.markdown("**📄 Sequential Navigation** (All Paragraphs)")
        seq_col1, seq_col2, seq_col3, seq_col4 = st.columns([1, 1, 1, 1])
        
        with seq_col1:
            if shortcut_button(
                "⬅️ Previous", 
                "arrowleft",
                disabled=current_index == 0, 
                key=f"seq_prev_{self.session_key}",
                help="Previous paragraph (← Arrow)"
            ):
                self.move_to_previous()
                st.rerun()
        
        with seq_col2:
            if shortcut_button(
                "➡️ Next", 
                "arrowright",
                disabled=current_index == self.total_items - 1, 
                key=f"seq_next_{self.session_key}",
                help="Next paragraph (→ Arrow)"
            ):
                self.move_to_next()
                st.rerun()
        
        with seq_col3:
            if shortcut_button(
                "⏮️ First", 
                "ctrl+arrowleft",
                key=f"seq_first_{self.session_key}",
                help="First paragraph (Ctrl+← Arrow)"
            ):
                st.session_state[self.session_key] = 0
                st.rerun()
        
        with seq_col4:
            if shortcut_button(
                "⏭️ Last", 
                "ctrl+arrowright",
                key=f"seq_last_{self.session_key}",
                help="Last paragraph (Ctrl+→ Arrow)"
            ):
                st.session_state[self.session_key] = self.total_items - 1
                st.rerun()
        
        # Unreviewed navigation row
        st.markdown("**🔍 Unreviewed Navigation** (Skip Completed)")
        unrev_col1, unrev_col2, unrev_col3, unrev_col4 = st.columns([1, 1, 1, 1])
        
        prev_unreviewed_idx = self.get_previous_unreviewed_index(current_index)
        next_unreviewed_idx = self.get_next_unreviewed_index(current_index)
        
        with unrev_col1:
            if shortcut_button(
                "⬅️ Prev Unreviewed", 
                "shift+arrowleft",
                disabled=prev_unreviewed_idx is None, 
                key=f"unrev_prev_{self.session_key}",
                help="Previous unreviewed paragraph (Shift+← Arrow)"
            ):
                if prev_unreviewed_idx is not None:
                    st.session_state[self.session_key] = prev_unreviewed_idx
                    st.rerun()
        
        with unrev_col2:
            if shortcut_button(
                "➡️ Next Unreviewed", 
                "shift+arrowright",
                disabled=next_unreviewed_idx is None, 
                key=f"unrev_next_{self.session_key}",
                help="Next unreviewed paragraph (Shift+→ Arrow)"
            ):
                if next_unreviewed_idx is not None:
                    st.session_state[self.session_key] = next_unreviewed_idx
                    st.rerun()
        
        with unrev_col3:
            # Find first unreviewed
            first_unreviewed = None
            for i, item in enumerate(self.items):
                if not item.get('reviewed', False):
                    first_unreviewed = i
                    break
            
            if shortcut_button(
                "⏮️ First Unreviewed", 
                "ctrl+shift+arrowleft",
                disabled=first_unreviewed is None, 
                key=f"unrev_first_{self.session_key}",
                help="First unreviewed paragraph (Ctrl+Shift+← Arrow)"
            ):
                if first_unreviewed is not None:
                    st.session_state[self.session_key] = first_unreviewed
                    st.rerun()
        
        with unrev_col4:
            # Find last unreviewed
            last_unreviewed = None
            for i in range(self.total_items - 1, -1, -1):
                if not self.items[i].get('reviewed', False):
                    last_unreviewed = i
                    break
            
            if shortcut_button(
                "⏭️ Last Unreviewed", 
                "ctrl+shift+arrowright",
                disabled=last_unreviewed is None, 
                key=f"unrev_last_{self.session_key}",
                help="Last unreviewed paragraph (Ctrl+Shift+→ Arrow)"
            ):
                if last_unreviewed is not None:
                    st.session_state[self.session_key] = last_unreviewed
                    st.rerun()
        
        # Additional controls row
        st.markdown("**⚡ Quick Actions**")
        quick_col1, quick_col2 = st.columns([1, 2])
        
        with quick_col1:
            if shortcut_button(
                "🔄 Refresh", 
                "f5",
                key=f"dual_refresh_{self.session_key}",
                help="Refresh page (F5)"
            ):
                st.rerun()
        
        with quick_col2:
            # Jump to specific paragraph
            jump_col1, jump_col2 = st.columns([3, 1])
            with jump_col1:
                jump_to = st.number_input(
                    "Jump to paragraph:", 
                    min_value=1, 
                    max_value=self.total_items,
                    value=current_index + 1, 
                    key=f"dual_jump_input_{self.session_key}"
                )
            with jump_col2:
                if shortcut_button(
                    "Go", 
                    "enter",
                    key=f"dual_go_{self.session_key}",
                    help="Jump to paragraph (Enter)"
                ):
                    st.session_state[self.session_key] = jump_to - 1
                    st.rerun()
        
        # Add shortcuts to jump input field
        add_shortcuts(
            **{f"dual_jump_input_{self.session_key}": "ctrl+j"}
        )
        
        self.render_fragmented_progress_bar()

    def render_fragmented_progress_bar(self) -> None:
        """Render a fragmented progress bar showing individual paragraph review status."""
        if not self.items:
            return
        
        current_index = self.get_current_index()
        
        # Create visual blocks representing each paragraph
        blocks = []
        for i, item in enumerate(self.items):
            if i == current_index:
                # Current paragraph - highlighted
                if item.get('reviewed', False):
                    blocks.append('🟦')  # Current + reviewed
                else:
                    blocks.append('🟨')  # Current + unreviewed
            else:
                # Other paragraphs
                if item.get('reviewed', False):
                    blocks.append('🟩')  # Reviewed
                else:
                    blocks.append('🟥')  # Unreviewed
        
        # Group blocks in rows of 50 for better display
        rows = []
        row_size = 98
        for i in range(0, len(blocks), row_size):
            row = ''.join(blocks[i:i+row_size])
            rows.append(row)
        
        # Display the progress bar
        st.markdown("**Visual Progress:**")
        for row in rows:
            st.markdown(f"`{row}`")
        
        # Legend
        legend_col1, legend_col2, legend_col3, legend_col4 = st.columns(4)
        with legend_col1:
            st.markdown("🟩 Reviewed")
        with legend_col2:
            st.markdown("🟥 Unreviewed")
        with legend_col3:
            st.markdown("🟨 Current")
        with legend_col4:
            st.markdown("🟦 Current + Reviewed")
