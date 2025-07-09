"""
Flashcard navigation component for the Conference Talks Analysis application.
"""
import streamlit as st
from typing import List, Any
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
        """Render enhanced navigation controls with better styling and keyboard shortcuts."""
        if not self.items:
            return
            
        current_index = self.get_current_index()
        
        # Enhanced navigation with progress bar
        progress = (current_index + 1) / self.total_items
        st.progress(progress, text=f"Flashcard {current_index + 1} of {self.total_items}")
        
        # Navigation buttons with keyboard shortcuts
        col1, col2, col3, col4, col5, col6 = st.columns([1, 1, 1, 1, 1, 2])
        
        with col1:
            if st.button(
                "⬅️ Previous", 
                disabled=current_index == 0,
                help="Previous flashcard (Left Arrow)",
                key=f"prev_{self.session_key}"
            ):
                st.session_state[self.session_key] = current_index - 1
                st.rerun()
        
        with col2:
            if st.button(
                "➡️ Next", 
                disabled=current_index == self.total_items - 1,
                help="Next flashcard (Right Arrow)",
                key=f"next_{self.session_key}"
            ):
                st.session_state[self.session_key] = current_index + 1
                st.rerun()
        
        with col3:
            if st.button(
                "🔄 Random",
                help="Random flashcard (R key)",
                key=f"random_{self.session_key}"
            ):
                st.session_state[self.session_key] = get_random_index(self.total_items)
                st.rerun()
        
        with col4:
            if st.button(
                "⏭️ First",
                help="Go to first flashcard",
                key=f"first_{self.session_key}"
            ):
                st.session_state[self.session_key] = 0
                st.rerun()
        
        with col5:
            if st.button(
                "⏮️ Last",
                help="Go to last flashcard",
                key=f"last_{self.session_key}"
            ):
                st.session_state[self.session_key] = self.total_items - 1
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
                    help="Enter a number to jump to that flashcard"
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