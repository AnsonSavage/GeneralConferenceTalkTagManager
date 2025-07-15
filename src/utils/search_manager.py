"""
Search and database population utilities.
"""
from typing import List, Dict
from .file_parser import FileParser
from .text_processor import TextProcessor
from ..database.base_database import BaseDatabaseInterface  


class SearchManager:
    """Handles searching files and populating the database with matching content."""
    
    def __init__(self, database: BaseDatabaseInterface, data_path: str):
        """
        Initialize the search manager.
        
        Args:
            database: The database instance to work with
            data_path: Path to the directory containing talk files
        """
        self.database = database
        self.file_parser = FileParser(data_path)
        self.text_processor = TextProcessor()
    
    def scan_for_keywords(self, keywords: List[str], match_whole_words: bool = True) -> List[Dict]:
        """
        Scan all text files for keywords and return matching paragraphs.
        
        Args:
            keywords: List of keywords to search for
            match_whole_words: Whether to match whole words only
            
        Returns:
            List of dictionaries containing match results
        """
        results = []
        talk_files = self.file_parser.get_all_talk_files()
        
        for file_path in talk_files:
            try:
                talk_data = self.file_parser.parse_talk_file(file_path)
                
                # Scan the talk content for keyword matches
                matches = self.text_processor.scan_text_for_keywords(
                    talk_data['content'], keywords, match_whole_words
                )
                
                # Add talk data to each match result
                for match in matches:
                    results.append({
                        'talk_data': talk_data,
                        'paragraph_number': match['paragraph_number'],
                        'content': match['content'],
                        'matched_keywords': match['matched_keywords']
                    })
            
            except Exception as e:
                print(f"Error processing file {file_path}: {e}")
                continue
        
        return results
    
    def search_and_populate_database(self, keywords: List[str], match_whole_words: bool = True) -> List[Dict]:
        """
        Search for keywords in files and populate database with matching content.
        
        Args:
            keywords: List of keywords to search for
            match_whole_words: Whether to match whole words only
            
        Returns:
            List of database paragraph records that were created/updated
        """
        # Add keywords to database
        self.database.add_keywords(keywords)
        
        # Scan files for matches
        scan_results = self.scan_for_keywords(keywords, match_whole_words=match_whole_words)
        
        # Add matching content to database
        database_results = []
        for result in scan_results:
            talk_data = result['talk_data']
            
            # Add or update talk
            talk_id = self.database.add_or_update_talk(talk_data)
            
            # Add or update paragraph
            paragraph_id = self.database.add_or_update_paragraph(
                talk_id, 
                result['paragraph_number'], 
                result['content'], 
                result['matched_keywords']
            )
            
            # Add keyword associations
            self.database.add_paragraph_keyword_associations(paragraph_id, result['matched_keywords'])
            
            # Prepare result for return
            database_results.append({
                'id': paragraph_id,
                'talk_id': talk_id,
                'paragraph_number': result['paragraph_number'],
                'content': result['content'],
                'matched_keywords': result['matched_keywords'],
                'notes': '',  # New paragraphs start with empty notes
                'reviewed': False,
                'review_date': None,
                'talk_title': talk_data['title'],
                'speaker': talk_data['speaker'],
                'conference_date': talk_data['conference_date'],
                'hyperlink': talk_data['url']
            })
        
        return database_results