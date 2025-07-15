"""
Text processing utilities for conference talk content.
"""
import re
from typing import List, Dict


class TextProcessor:
    """Handles text processing operations like paragraph splitting and keyword matching."""
    
    def split_into_paragraphs(self, content: str) -> List[str]:
        """
        Split talk content into paragraphs.
        
        Args:
            content: The full text content to split
            
        Returns:
            List of paragraph strings
        """
        # Split by double newlines or single newlines followed by significant whitespace
        paragraphs = re.split(r'\n\s*\n|\n(?=\s{2,})', content)
        
        # Clean up paragraphs
        cleaned_paragraphs = []
        for para in paragraphs:
            # Remove extra whitespace and newlines
            cleaned = ' '.join(para.split())
            # Only keep paragraphs with substantial content
            if len(cleaned) > 50:  # Minimum paragraph length
                cleaned_paragraphs.append(cleaned)
        
        return cleaned_paragraphs
    
    def find_keyword_matches(self, text: str, keywords: List[str], match_whole_words: bool = True) -> List[str]:
        """
        Find which keywords match in the given text.
        
        Args:
            text: The text to search in
            keywords: List of keywords to search for
            match_whole_words: Whether to match whole words only
            
        Returns:
            List of keywords that were found in the text
        """
        matched_keywords = []
        text_lower = text.lower()
        
        if match_whole_words:
            # Use regex patterns for whole word matching
            for keyword in keywords:
                pattern = re.compile(rf'\b{re.escape(keyword)}\b', re.IGNORECASE)
                if pattern.search(text):
                    matched_keywords.append(keyword)
        else:
            # Simple substring matching
            for keyword in keywords:
                if keyword.lower() in text_lower:
                    matched_keywords.append(keyword)
        
        return matched_keywords
    
    def scan_text_for_keywords(self, content: str, keywords: List[str], match_whole_words: bool = True) -> List[Dict]:
        """
        Scan text content for keywords and return matching paragraphs with their matches.
        
        Args:
            content: The full text content to scan
            keywords: List of keywords to search for
            match_whole_words: Whether to match whole words only
            
        Returns:
            List of dictionaries containing paragraph info and matched keywords
        """
        paragraphs = self.split_into_paragraphs(content)
        results = []
        
        for para_num, paragraph in enumerate(paragraphs, 1):
            matched_keywords = self.find_keyword_matches(paragraph, keywords, match_whole_words)
            
            if matched_keywords:
                results.append({
                    'paragraph_number': para_num,
                    'content': paragraph,
                    'matched_keywords': matched_keywords
                })
        
        return results