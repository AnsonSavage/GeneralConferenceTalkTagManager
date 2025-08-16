"""
SQLite implementation of the conference talks database.
"""
import sqlite3
import json
from datetime import datetime, date
from typing import List, Dict, Any, override

from .base_database import BaseDatabaseInterface


class SQLiteConferenceTalksDB(BaseDatabaseInterface):
    """SQLite implementation of the conference talks database."""
    
    def __init__(self, connection_params: Dict[str, Any]) -> None:
        """
        Initialize the SQLite database connection.
        
        Args:
            connection_params: Should contain 'db_path' key
        """
        super().__init__(connection_params)
        self.db_path = connection_params.get('db_path', 'conference_talks.db')
        self.init_database()

    def _parse_conference_date(self, date_string: str) -> date:
        """Convert conference date string to date object."""
        if isinstance(date_string, date):
            return date_string
        
        # Handle existing format like "April 2023" or "October 2023"
        if isinstance(date_string, str):
            parts = date_string.strip().split()
            if len(parts) == 2:
                month_str, year_str = parts
                year = int(year_str)
                month = 4 if month_str.lower() == 'april' else 10
                return date(year, month, 1)
        
        # Fallback for any other format
        return date.today()

    def _format_conference_date(self, date_obj: date) -> str:
        """Convert date object to display string."""
        if isinstance(date_obj, str):
            return date_obj  # Already formatted
        
        month_name = "April" if date_obj.month == 4 else "October"
        return f"{month_name} {date_obj.year}"

    @override
    def init_database(self) -> None:
        """Initialize the database with tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create tables
        cursor.executescript("""
            CREATE TABLE IF NOT EXISTS talks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                speaker TEXT NOT NULL,
                conference_date DATE NOT NULL,
                hyperlink TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            CREATE TABLE IF NOT EXISTS paragraphs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                talk_id INTEGER NOT NULL,
                paragraph_number INTEGER NOT NULL,
                content TEXT NOT NULL,
                matched_keywords TEXT, -- JSON array of keywords
                notes TEXT, -- User notes for this paragraph
                reviewed BOOLEAN DEFAULT FALSE,
                review_date TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (talk_id) REFERENCES talks (id) ON DELETE CASCADE
            );
            
            CREATE TABLE IF NOT EXISTS tags (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                parent_tag_id INTEGER,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (parent_tag_id) REFERENCES tags (id) ON DELETE SET NULL
            );
            
            CREATE TABLE IF NOT EXISTS paragraph_tags (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                paragraph_id INTEGER NOT NULL,
                tag_id INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (paragraph_id) REFERENCES paragraphs (id) ON DELETE CASCADE,
                FOREIGN KEY (tag_id) REFERENCES tags (id) ON DELETE CASCADE,
                UNIQUE(paragraph_id, tag_id)
            );
            
            CREATE TABLE IF NOT EXISTS keywords (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                keyword TEXT UNIQUE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            CREATE TABLE IF NOT EXISTS paragraph_keywords (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                paragraph_id INTEGER NOT NULL,
                keyword_id INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (paragraph_id) REFERENCES paragraphs (id) ON DELETE CASCADE,
                FOREIGN KEY (keyword_id) REFERENCES keywords (id) ON DELETE CASCADE,
                UNIQUE(paragraph_id, keyword_id)
            );
          
            -- Indexes for better performance
            CREATE INDEX IF NOT EXISTS idx_paragraphs_talk_id ON paragraphs(talk_id);
            CREATE INDEX IF NOT EXISTS idx_paragraphs_reviewed ON paragraphs(reviewed);
            CREATE INDEX IF NOT EXISTS idx_paragraph_tags_paragraph_id ON paragraph_tags(paragraph_id);
            CREATE INDEX IF NOT EXISTS idx_paragraph_tags_tag_id ON paragraph_tags(tag_id);
            CREATE INDEX IF NOT EXISTS idx_paragraph_keywords_paragraph_id ON paragraph_keywords(paragraph_id);
            CREATE INDEX IF NOT EXISTS idx_paragraph_keywords_keyword_id ON paragraph_keywords(keyword_id);
            CREATE INDEX IF NOT EXISTS idx_tags_parent ON tags(parent_tag_id);
            CREATE INDEX IF NOT EXISTS idx_talks_conference_date ON talks(conference_date);
        """)
        
        conn.commit()
        conn.close()
    
    @override
    def add_talk(self, title: str, speaker: str, conference_date: str, 
                 hyperlink: str) -> int:
        """Add a new talk and return its ID"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Convert conference_date to date object
        date_obj = self._parse_conference_date(conference_date)
        
        cursor.execute("""
            INSERT INTO talks (title, speaker, conference_date, hyperlink)
            VALUES (?, ?, ?, ?)
        """, (title, speaker, date_obj.isoformat(), hyperlink))
        
        talk_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return talk_id
    
    @override
    def add_or_update_talk(self, talk_data: Dict) -> int:
        """Add a talk to the database or return existing ID"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Check if talk already exists (by title and speaker)
        cursor.execute("""
            SELECT id FROM talks 
            WHERE title = ? AND speaker = ?
        """, (talk_data['title'], talk_data['speaker']))
        
        existing = cursor.fetchone()
        if existing:
            talk_id = existing[0]
        else:
            # Convert conference_date to date object
            date_obj = self._parse_conference_date(talk_data['conference_date'])
            
            # Add new talk
            cursor.execute("""
                INSERT INTO talks (title, speaker, conference_date, hyperlink)
                VALUES (?, ?, ?, ?)
            """, (talk_data['title'], talk_data['speaker'], date_obj.isoformat(), 
                  talk_data.get('url', talk_data.get('hyperlink'))))
            talk_id = cursor.lastrowid
        
        conn.commit()
        conn.close()
        return talk_id
    
    @override
    def get_talks_summary(self) -> List[Dict]:
        """Get summary of all talks"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                t.id, t.title, t.speaker, t.conference_date, t.hyperlink,
                COUNT(p.id) as paragraph_count,
                COUNT(CASE WHEN p.reviewed = 1 THEN 1 END) as reviewed_count
            FROM talks t
            LEFT JOIN paragraphs p ON t.id = p.talk_id
            GROUP BY t.id, t.title, t.speaker, t.conference_date, t.hyperlink
            ORDER BY t.conference_date DESC, t.title
        """)
        
        rows = cursor.fetchall()
        talks = []
        for row in rows:
            # Convert date back to display format
            conference_date = datetime.fromisoformat(row[3]).date() if row[3] else None
            talks.append({
                'id': row[0],
                'title': row[1],
                'speaker': row[2],
                'conference_date': self._format_conference_date(conference_date) if conference_date else '',
                'hyperlink': row[4],
                'paragraph_count': row[5],
                'reviewed_count': row[6]
            })
        
        conn.close()
        return talks
    
    @override
    def get_talks_with_paragraph_counts(self) -> List[Dict]:
        """Get all talks with their paragraph counts."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT t.id, t.title, t.speaker, t.conference_date, t.hyperlink,
                   COUNT(p.id) as total_paragraphs
            FROM talks t
            LEFT JOIN paragraphs p ON t.id = p.talk_id
            GROUP BY t.id, t.title, t.speaker, t.conference_date, t.hyperlink
            ORDER BY t.conference_date DESC, t.title
        """)
        
        rows = cursor.fetchall()
        talks = []
        for row in rows:
            # Convert date back to display format
            conference_date = datetime.fromisoformat(row[3]).date() if row[3] else None
            talks.append({
                'id': row[0],
                'title': row[1],
                'speaker': row[2],
                'conference_date': self._format_conference_date(conference_date) if conference_date else '',
                'hyperlink': row[4],
                'total_paragraphs': row[5]
            })
        
        conn.close()
        return talks
    
    @override
    def add_paragraph(self, talk_id: int, paragraph_number: int, 
                     content: str, matched_keywords: List[str] = None) -> int:
        """Add a paragraph to a talk"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        keywords_json = json.dumps(matched_keywords) if matched_keywords else None
        
        cursor.execute("""
            INSERT INTO paragraphs (talk_id, paragraph_number, content, matched_keywords)
            VALUES (?, ?, ?, ?)
        """, (talk_id, paragraph_number, content, keywords_json))
        
        paragraph_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return paragraph_id
    
    @override
    def add_or_update_paragraph(self, talk_id: int, paragraph_number: int, 
                               content: str, matched_keywords: List[str]) -> int:
        """Add a paragraph or update its keywords if it already exists"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Check if paragraph already exists
        cursor.execute("""
            SELECT id, matched_keywords FROM paragraphs 
            WHERE talk_id = ? AND paragraph_number = ?
        """, (talk_id, paragraph_number))
        
        existing = cursor.fetchone()
        if existing:
            paragraph_id = existing[0]
            existing_keywords = json.loads(existing[1]) if existing[1] else []
            
            # Merge keywords (avoid duplicates)
            all_keywords = list(set(existing_keywords + matched_keywords))
            
            # Update the paragraph with merged keywords
            cursor.execute("""
                UPDATE paragraphs 
                SET matched_keywords = ?, content = ?
                WHERE id = ?
            """, (json.dumps(all_keywords), content, paragraph_id))
        else:
            # Add new paragraph
            cursor.execute("""
                INSERT INTO paragraphs (talk_id, paragraph_number, content, matched_keywords)
                VALUES (?, ?, ?, ?)
            """, (talk_id, paragraph_number, content, json.dumps(matched_keywords)))
            paragraph_id = cursor.lastrowid
        
        conn.commit()
        conn.close()
        return paragraph_id
    
    @override
    def add_tag(self, name: str, description: str = None, parent_tag_id: int = None) -> int:
        """Add a new tag"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO tags (name, description, parent_tag_id)
                VALUES (?, ?, ?)
            """, (name, description, parent_tag_id))
            
            tag_id = cursor.lastrowid
            conn.commit()
            conn.close()
            return tag_id
        except sqlite3.IntegrityError:
            conn.close()
            raise ValueError(f"Tag '{name}' already exists")
    
    @override
    def tag_paragraph(self, paragraph_id: int, tag_id: int) -> None:
        """Tag a paragraph with a specific tag"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO paragraph_tags (paragraph_id, tag_id)
                VALUES (?, ?)
            """, (paragraph_id, tag_id))
            conn.commit()
        except sqlite3.IntegrityError:
            pass  # Tag already exists for this paragraph
        finally:
            conn.close()
    
    @override
    def remove_tag_from_paragraph(self, paragraph_id: int, tag_id: int) -> None:
        """Remove a tag from a paragraph"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            DELETE FROM paragraph_tags 
            WHERE paragraph_id = ? AND tag_id = ?
        """, (paragraph_id, tag_id))
        
        conn.commit()
        conn.close()
    
    @override
    def search_paragraphs(self, keywords: List[str]) -> List[Dict]:
        """Search for paragraphs containing any of the keywords"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create a search condition for each keyword
        conditions = []
        params = []
        
        for keyword in keywords:
            conditions.append("p.content LIKE ?")
            params.append(f"%{keyword}%")
        
        where_clause = " OR ".join(conditions)
        
        query = f"""
            SELECT 
                p.id, p.talk_id, p.paragraph_number, p.content, 
                p.matched_keywords, p.notes, p.reviewed, p.review_date,
                t.title, t.speaker, t.conference_date, t.hyperlink
            FROM paragraphs p
            JOIN talks t ON p.talk_id = t.id
            WHERE {where_clause}
            ORDER BY t.conference_date, t.title, p.paragraph_number
        """
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        results = []
        for row in rows:
            # Find which keywords actually matched
            actual_matches = []
            content_lower = row[3].lower()
            for keyword in keywords:
                if keyword.lower() in content_lower:
                    actual_matches.append(keyword)
            
            # Convert date back to display format
            conference_date = datetime.fromisoformat(row[10]).date() if row[10] else None
            
            results.append({
                'id': row[0],
                'talk_id': row[1],
                'paragraph_number': row[2],
                'content': row[3],
                'matched_keywords': actual_matches,
                'notes': row[5] or '',
                'reviewed': bool(row[6]),
                'review_date': row[7],
                'talk_title': row[8],
                'speaker': row[9],
                'conference_date': self._format_conference_date(conference_date) if conference_date else '',
                'hyperlink': row[11]
            })
        
        conn.close()
        return results
    
    @override
    def get_paragraph_tags(self, paragraph_id: int) -> List[Dict]:
        """Get all tags for a paragraph"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT t.id, t.name, t.description, t.parent_tag_id
            FROM tags t
            JOIN paragraph_tags pt ON t.id = pt.tag_id
            WHERE pt.paragraph_id = ?
            ORDER BY t.name
        """, (paragraph_id,))
        
        rows = cursor.fetchall()
        tags = [{'id': row[0], 'name': row[1], 'description': row[2], 'parent_tag_id': row[3]} 
                for row in rows]
        
        conn.close()
        return tags
    
    @override
    def get_all_tags(self) -> List[Dict]:
        """Get all tags with their hierarchy"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, name, description, parent_tag_id
            FROM tags
            ORDER BY name
        """)
        
        rows = cursor.fetchall()
        tags = [{'id': row[0], 'name': row[1], 'description': row[2], 'parent_tag_id': row[3]} 
                for row in rows]
        
        conn.close()
        return tags
    
    @override
    def mark_paragraph_reviewed(self, paragraph_id: int, reviewed: bool = True) -> None:
        """Mark a paragraph as reviewed"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        review_date = datetime.now().isoformat() if reviewed else None
        
        cursor.execute("""
            UPDATE paragraphs 
            SET reviewed = ?, review_date = ?
            WHERE id = ?
        """, (reviewed, review_date, paragraph_id))
        
        conn.commit()
        conn.close()
    
    @override
    def mark_all_paragraphs_not_reviewed(self) -> None:
        """Mark all paragraphs as not reviewed."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE paragraphs SET reviewed = 0, review_date = NULL WHERE reviewed = 1"
        )
        conn.commit()
        conn.close()

    @override
    def delete_tag(self, tag_id: int) -> None:
        """Delete a tag and update its children to have no parent"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Update children to have no parent
        cursor.execute("UPDATE tags SET parent_tag_id = NULL WHERE parent_tag_id = ?", (tag_id,))
        
        # Delete the tag (this will cascade to paragraph_tags)
        cursor.execute("DELETE FROM tags WHERE id = ?", (tag_id,))
        
        conn.commit()
        conn.close()
    
    @override
    def search_tags(self, query: str) -> List[Dict]:
        """Search for tags by name"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, name, description, parent_tag_id
            FROM tags
            WHERE name LIKE ?
            ORDER BY name
        """, (f"%{query}%",))
        
        rows = cursor.fetchall()
        tags = [{'id': row[0], 'name': row[1], 'description': row[2], 'parent_tag_id': row[3]} 
                for row in rows]
        
        conn.close()
        return tags
    
    # Database-specific query methods (to replace direct SQL calls)
    @override
    def get_paragraph_count_for_tag(self, tag_id: int) -> int:
        """Get the number of paragraphs assigned to a specific tag."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM paragraph_tags WHERE tag_id = ?", (tag_id,))
        count = cursor.fetchone()[0]
        conn.close()
        return count
    
    @override
    def remove_tag_from_all_paragraphs(self, tag_id: int) -> int:
        """Remove a tag from all paragraphs and return the number of paragraphs affected."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # First get the count
        cursor.execute("SELECT COUNT(*) FROM paragraph_tags WHERE tag_id = ?", (tag_id,))
        count = cursor.fetchone()[0]
        
        # Then remove the associations
        cursor.execute("DELETE FROM paragraph_tags WHERE tag_id = ?", (tag_id,))
        conn.commit()
        conn.close()
        return count
    
    @override
    def get_export_statistics(self) -> Dict[str, Any]:
        """Get comprehensive statistics for export preview."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Tag statistics
        cursor.execute("SELECT COUNT(*) FROM tags")
        total_tags = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM tags WHERE parent_tag_id IS NULL")
        root_tags = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM tags WHERE parent_tag_id IS NOT NULL")
        child_tags = cursor.fetchone()[0]
        
        # Paragraph statistics
        cursor.execute("SELECT COUNT(*) FROM paragraphs")
        total_paragraphs = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(DISTINCT paragraph_id) FROM paragraph_tags")
        tagged_paragraphs = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM paragraphs WHERE notes IS NOT NULL AND notes != ''")
        paragraphs_with_notes = cursor.fetchone()[0]
        
        # Keyword statistics
        cursor.execute("SELECT COUNT(*) FROM keywords")
        total_keywords = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(DISTINCT keyword_id) FROM paragraph_keywords")
        used_keywords = cursor.fetchone()[0]
        
        # Talk statistics
        cursor.execute("SELECT COUNT(*) FROM talks")
        total_talks = cursor.fetchone()[0]
        
        cursor.execute(
            """
            SELECT COUNT(DISTINCT t.id)
            FROM talks t
            JOIN paragraphs p ON t.id = p.talk_id
            JOIN paragraph_tags pt ON p.id = pt.paragraph_id
            """
        )
        tagged_talks = cursor.fetchone()[0]
        
        conn.close()
        return {
            'total_tags': total_tags,
            'root_tags': root_tags,
            'child_tags': child_tags,
            'total_paragraphs': total_paragraphs,
            'tagged_paragraphs': tagged_paragraphs,
            'untagged_paragraphs': total_paragraphs - tagged_paragraphs,
            'paragraphs_with_notes': paragraphs_with_notes,
            'total_keywords': total_keywords,
            'used_keywords': used_keywords,
            'total_talks': total_talks,
            'tagged_talks': tagged_talks,
        }
    
    @override
    def get_database_info(self) -> Dict[str, Any]:
        """Get database metadata and table information."""
        import os
        from datetime import datetime
        
        info = {
            'db_path': self.db_path,
            'tables': {}
        }
        
        # File information
        if os.path.exists(self.db_path):
            info['file_size'] = os.path.getsize(self.db_path)
            info['last_modified'] = datetime.fromtimestamp(os.path.getmtime(self.db_path))
        
        # Table information
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tables = cursor.fetchall()
        
        for table in tables:
            table_name = table[0]
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            info['tables'][table_name] = count
        
        conn.close()
        return info
    
    @override
    def get_top_tags_by_usage(self, limit: int = 10) -> List[Dict]:
        """Get top tags by paragraph count."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT t.id, t.name, t.description, COUNT(pt.paragraph_id) as usage_count
            FROM tags t
            LEFT JOIN paragraph_tags pt ON t.id = pt.tag_id
            GROUP BY t.id, t.name, t.description
            ORDER BY usage_count DESC, t.name
            LIMIT ?
        """, (limit,))
        
        rows = cursor.fetchall()
        top_tags = []
        for row in rows:
            top_tags.append({
                'id': row[0],
                'name': row[1],
                'description': row[2],
                'usage_count': row[3]
            })
        
        conn.close()
        return top_tags
    
    @override
    def get_all_paragraphs_with_filters(self, tag_filter: str = None, keyword_filter: str = None, untagged_only: bool = False, reviewed_only: bool = False) -> List[Dict]:
        """Get paragraphs with optional filtering."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Build the query based on filters
        base_query = """
            SELECT DISTINCT
                p.id, p.talk_id, p.paragraph_number, p.content, 
                p.matched_keywords, p.notes, p.reviewed, p.review_date,
                t.title, t.speaker, t.conference_date, t.hyperlink
            FROM paragraphs p
            JOIN talks t ON p.talk_id = t.id
        """
        
        conditions = []
        params = []
        
        if tag_filter:
            base_query += " JOIN paragraph_tags pt ON p.id = pt.paragraph_id JOIN tags tag ON pt.tag_id = tag.id"
            conditions.append("tag.name LIKE ?")
            params.append(f"%{tag_filter}%")
        
        if keyword_filter:
            conditions.append("(p.content LIKE ? OR p.matched_keywords LIKE ?)")
            params.extend([f"%{keyword_filter}%", f"%{keyword_filter}%"])
        
        if untagged_only:
            conditions.append("p.id NOT IN (SELECT paragraph_id FROM paragraph_tags)")
        
        if reviewed_only:
            conditions.append("p.reviewed = 1")
        
        if conditions:
            base_query += " WHERE " + " AND ".join(conditions)
        
        base_query += " ORDER BY t.conference_date, t.title, p.paragraph_number"
        
        cursor.execute(base_query, params)
        rows = cursor.fetchall()
        
        results = []
        for row in rows:
            matched_keywords = json.loads(row[4]) if row[4] else []
            # Convert date back to display format
            conference_date = datetime.fromisoformat(row[10]).date() if row[10] else None
            results.append({
                'id': row[0],
                'talk_id': row[1],
                'paragraph_number': row[2],
                'content': row[3],
                'matched_keywords': matched_keywords,
                'notes': row[5] or '',
                'reviewed': bool(row[6]),
                'review_date': row[7],
                'talk_title': row[8],
                'speaker': row[9],
                'conference_date': self._format_conference_date(conference_date) if conference_date else '',
                'hyperlink': row[11]
            })
        
        conn.close()
        return results
    
    @override
    def get_paragraphs_by_tag(self, tag_id: int) -> List[Dict]:
        """Get all paragraphs that have a specific tag."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                p.id, p.talk_id, p.paragraph_number, p.content, 
                p.matched_keywords, p.notes, p.reviewed, p.review_date,
                t.title, t.speaker, t.conference_date, t.hyperlink
            FROM paragraphs p
            JOIN talks t ON p.talk_id = t.id
            JOIN paragraph_tags pt ON p.id = pt.paragraph_id
            WHERE pt.tag_id = ?
            ORDER BY t.conference_date, t.title, p.paragraph_number
        """, (tag_id,))
        
        rows = cursor.fetchall()
        results = []
        for row in rows:
            matched_keywords = json.loads(row[4]) if row[4] else []
            # Convert date back to display format
            conference_date = datetime.fromisoformat(row[10]).date() if row[10] else None
            results.append({
                'id': row[0],
                'talk_id': row[1],
                'paragraph_number': row[2],
                'content': row[3],
                'matched_keywords': matched_keywords,
                'notes': row[5] or '',
                'reviewed': bool(row[6]),
                'review_date': row[7],
                'talk_title': row[8],
                'speaker': row[9],
                'conference_date': self._format_conference_date(conference_date) if conference_date else '',
                'hyperlink': row[11]
            })
        
        conn.close()
        return results
    
    @override
    def get_paragraph_tags_with_hierarchy(self, paragraph_id: int) -> Dict:
        """Get all tags for a paragraph, separating explicit and implicit tags."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get explicitly assigned tags
        cursor.execute("""
            SELECT t.id, t.name, t.description, t.parent_tag_id
            FROM tags t
            JOIN paragraph_tags pt ON t.id = pt.tag_id
            WHERE pt.paragraph_id = ?
            ORDER BY t.name
        """, (paragraph_id,))
        
        explicit_tags = []
        for row in cursor.fetchall():
            explicit_tags.append({
                'id': row[0],
                'name': row[1],
                'description': row[2],
                'parent_tag_id': row[3]
            })
        
        # Get all parent tags (implicit tags)
        all_tag_ids = set()
        for tag in explicit_tags:
            hierarchy = self.get_tag_hierarchy(tag['id'])
            all_tag_ids.update(hierarchy)
        
        # Remove explicit tag IDs to get only implicit ones
        explicit_tag_ids = {tag['id'] for tag in explicit_tags}
        implicit_tag_ids = all_tag_ids - explicit_tag_ids
        
        # Get implicit tag details
        implicit_tags = []
        if implicit_tag_ids:
            placeholders = ','.join(['?'] * len(implicit_tag_ids))
            cursor.execute(f"""
                SELECT id, name, description, parent_tag_id
                FROM tags
                WHERE id IN ({placeholders})
                ORDER BY name
            """, list(implicit_tag_ids))
            
            for row in cursor.fetchall():
                implicit_tags.append({
                    'id': row[0],
                    'name': row[1],
                    'description': row[2],
                    'parent_tag_id': row[3]
                })
        
        conn.close()
        return {
            'explicit_tags': explicit_tags,
            'implicit_tags': implicit_tags
        }
    
    @override
    def update_tag(self, tag_id: int, name: str = None, description: str = None, parent_tag_id: int = None) -> None:
        """Update a tag's properties."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        updates = []
        params = []
        
        if name is not None:
            updates.append("name = ?")
            params.append(name)
        
        if description is not None:
            updates.append("description = ?")
            params.append(description)
        
        if parent_tag_id is not None:
            updates.append("parent_tag_id = ?")
            params.append(parent_tag_id)
        
        if updates:
            params.append(tag_id)
            query = f"UPDATE tags SET {', '.join(updates)} WHERE id = ?"
            cursor.execute(query, params)
            conn.commit()
        
        conn.close()
    
    @override
    def get_tag_hierarchy(self, tag_id: int) -> List[int]:
        """Get all parent tags for a given tag (including the tag itself)."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        hierarchy = []
        current_id = tag_id
        
        while current_id:
            hierarchy.append(current_id)
            cursor.execute("SELECT parent_tag_id FROM tags WHERE id = ?", (current_id,))
            result = cursor.fetchone()
            current_id = result[0] if result else None
        
        conn.close()
        return hierarchy
    
    @override
    def get_paragraph_with_notes(self, paragraph_id: int) -> Dict:
        """Get a paragraph with its notes."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                p.id, p.talk_id, p.paragraph_number, p.content, 
                p.matched_keywords, p.notes, p.reviewed, p.review_date,
                t.title, t.speaker, t.conference_date, t.hyperlink
            FROM paragraphs p
            JOIN talks t ON p.talk_id = t.id
            WHERE p.id = ?
        """, (paragraph_id,))
        
        row = cursor.fetchone()
        if not row:
            conn.close()
            return None
        
        matched_keywords = json.loads(row[4]) if row[4] else []
        # Convert date back to display format
        conference_date = datetime.fromisoformat(row[10]).date() if row[10] else None
        result = {
            'id': row[0],
            'talk_id': row[1],
            'paragraph_number': row[2],
            'content': row[3],
            'matched_keywords': matched_keywords,
            'notes': row[5] or '',
            'reviewed': bool(row[6]),
            'review_date': row[7],
            'talk_title': row[8],
            'speaker': row[9],
            'conference_date': self._format_conference_date(conference_date) if conference_date else '',
            'hyperlink': row[11]
        }
        
        conn.close()
        return result
    
    @override
    def get_untagged_paragraphs_summary(self) -> Dict[str, Any]:
        """Get summary statistics for untagged paragraphs."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT COUNT(*) FROM paragraphs 
            WHERE id NOT IN (SELECT DISTINCT paragraph_id FROM paragraph_tags)
        """)
        untagged_count = cursor.fetchone()[0]
        
        cursor.execute("""
            SELECT COUNT(*) FROM paragraphs 
            WHERE id NOT IN (SELECT DISTINCT paragraph_id FROM paragraph_tags)
            AND reviewed = 1
        """)
        untagged_reviewed = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM paragraphs")
        total_paragraphs = cursor.fetchone()[0]
        
        conn.close()
        return {
            'total_paragraphs': total_paragraphs,
            'untagged_count': untagged_count,
            'untagged_reviewed': untagged_reviewed,
            'untagged_percentage': (untagged_count / total_paragraphs * 100) if total_paragraphs > 0 else 0
        }
    
    @override
    def get_tag_usage_statistics(self) -> List[Dict]:
        """Get usage statistics for all tags."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT t.id, t.name, t.description, t.parent_tag_id,
                   COUNT(pt.paragraph_id) as usage_count
            FROM tags t
            LEFT JOIN paragraph_tags pt ON t.id = pt.tag_id
            GROUP BY t.id, t.name, t.description, t.parent_tag_id
            ORDER BY usage_count DESC, t.name
        """)
        
        rows = cursor.fetchall()
        stats = []
        for row in rows:
            stats.append({
                'id': row[0],
                'name': row[1],
                'description': row[2],
                'parent_tag_id': row[3],
                'usage_count': row[4]
            })
        
        conn.close()
        return stats
    
    @override
    def add_keywords(self, keywords: List[str]) -> None:
        """Add keywords to the keywords table."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for keyword in keywords:
            try:
                cursor.execute("INSERT INTO keywords (keyword) VALUES (?)", (keyword,))
            except sqlite3.IntegrityError:
                pass  # Keyword already exists
        
        conn.commit()
        conn.close()
    
    @override
    def get_keywords(self) -> List[str]:
        """Get all keywords."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT keyword FROM keywords ORDER BY keyword")
        keywords = [row[0] for row in cursor.fetchall()]
        
        conn.close()
        return keywords
    
    @override
    def delete_keyword(self, keyword: str) -> None:
        """Delete a keyword and all its associations."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Delete associations first (will be handled by foreign key cascade)
        cursor.execute("DELETE FROM keywords WHERE keyword = ?", (keyword,))
        
        conn.commit()
        conn.close()
    
    @override
    def get_paragraphs_by_keyword(self, keyword: str) -> List[Dict]:
        """Get all paragraphs that match a specific keyword."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                p.id, p.talk_id, p.paragraph_number, p.content, 
                p.matched_keywords, p.notes, p.reviewed, p.review_date,
                t.title, t.speaker, t.conference_date, t.hyperlink
            FROM paragraphs p
            JOIN talks t ON p.talk_id = t.id
            JOIN paragraph_keywords pk ON p.id = pk.paragraph_id
            JOIN keywords k ON pk.keyword_id = k.id
            WHERE k.keyword = ?
            ORDER BY t.conference_date, t.title, p.paragraph_number
        """, (keyword,))
        
        rows = cursor.fetchall()
        results = []
        for row in rows:
            matched_keywords = json.loads(row[4]) if row[4] else []
            # Convert date back to display format
            conference_date = datetime.fromisoformat(row[10]).date() if row[10] else None
            results.append({
                'id': row[0],
                'talk_id': row[1],
                'paragraph_number': row[2],
                'content': row[3],
                'matched_keywords': matched_keywords,
                'notes': row[5] or '',
                'reviewed': bool(row[6]),
                'review_date': row[7],
                'talk_title': row[8],
                'speaker': row[9],
                'conference_date': self._format_conference_date(conference_date) if conference_date else '',
                'hyperlink': row[11]
            })
        
        conn.close()
        return results
    
    @override
    def add_paragraph_keyword_associations(self, paragraph_id: int, keywords: List[str]) -> None:
        """Add keyword associations for a paragraph."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for keyword in keywords:
            # Get keyword ID
            cursor.execute("SELECT id FROM keywords WHERE keyword = ?", (keyword,))
            result = cursor.fetchone()
            if result:
                keyword_id = result[0]
                try:
                    cursor.execute("""
                        INSERT INTO paragraph_keywords (paragraph_id, keyword_id)
                        VALUES (?, ?)
                    """, (paragraph_id, keyword_id))
                except sqlite3.IntegrityError:
                    pass  # Association already exists
        
        conn.commit()
        conn.close()
    
    @override
    def get_keyword_usage_statistics(self) -> List[Dict]:
        """Get usage statistics for all keywords."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT k.keyword, COUNT(pk.paragraph_id) as usage_count
            FROM keywords k
            LEFT JOIN paragraph_keywords pk ON k.id = pk.keyword_id
            GROUP BY k.keyword
            ORDER BY usage_count DESC, k.keyword
        """)
        
        rows = cursor.fetchall()
        stats = []
        for row in rows:
            stats.append({
                'keyword': row[0],
                'usage_count': row[1]
            })
        
        conn.close()
        return stats
    
    @override
    def update_paragraph_notes(self, paragraph_id: int, notes: str) -> None:
        """Update notes for a paragraph."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE paragraphs 
            SET notes = ?
            WHERE id = ?
        """, (notes, paragraph_id))
        
        conn.commit()
        conn.close()