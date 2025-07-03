import sqlite3
import json
import os
import re
from datetime import datetime
from typing import List, Dict, Optional, Tuple

class ConferenceTalksDB:
    def __init__(self, db_path: str = "conference_talks.db", data_path: str = "data/General_Conference_Talks"):
        self.db_path = db_path
        self.data_path = data_path
        self.init_database()
    
    def init_database(self):
        """Initialize the database with tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create tables
        cursor.executescript("""
            CREATE TABLE IF NOT EXISTS talks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                speaker TEXT NOT NULL,
                conference_date TEXT NOT NULL,
                session TEXT,
                hyperlink TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            CREATE TABLE IF NOT EXISTS paragraphs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                talk_id INTEGER NOT NULL,
                paragraph_number INTEGER NOT NULL,
                content TEXT NOT NULL,
                matched_keywords TEXT, -- JSON array of keywords
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
            
            CREATE TABLE IF NOT EXISTS search_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                search_keywords TEXT NOT NULL, -- JSON array
                results_count INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            -- Indexes for better performance
            CREATE INDEX IF NOT EXISTS idx_paragraphs_talk_id ON paragraphs(talk_id);
            CREATE INDEX IF NOT EXISTS idx_paragraphs_reviewed ON paragraphs(reviewed);
            CREATE INDEX IF NOT EXISTS idx_paragraph_tags_paragraph_id ON paragraph_tags(paragraph_id);
            CREATE INDEX IF NOT EXISTS idx_paragraph_tags_tag_id ON paragraph_tags(tag_id);
            CREATE INDEX IF NOT EXISTS idx_paragraph_keywords_paragraph_id ON paragraph_keywords(paragraph_id);
            CREATE INDEX IF NOT EXISTS idx_paragraph_keywords_keyword_id ON paragraph_keywords(keyword_id);
            CREATE INDEX IF NOT EXISTS idx_tags_parent ON tags(parent_tag_id);
        """)
        
        conn.commit()
        conn.close()
    
    def add_talk(self, title: str, speaker: str, conference_date: str, 
                 hyperlink: str, session: str = None) -> int:
        """Add a new talk and return its ID"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO talks (title, speaker, conference_date, session, hyperlink)
            VALUES (?, ?, ?, ?, ?)
        """, (title, speaker, conference_date, session, hyperlink))
        
        talk_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return talk_id
    
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
    
    def tag_paragraph(self, paragraph_id: int, tag_id: int):
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
    
    def remove_tag_from_paragraph(self, paragraph_id: int, tag_id: int):
        """Remove a tag from a paragraph"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            DELETE FROM paragraph_tags 
            WHERE paragraph_id = ? AND tag_id = ?
        """, (paragraph_id, tag_id))
        
        conn.commit()
        conn.close()
    
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
                p.matched_keywords, p.reviewed, p.review_date,
                t.title, t.speaker, t.conference_date, t.session, t.hyperlink
            FROM paragraphs p
            JOIN talks t ON p.talk_id = t.id
            WHERE {where_clause}
            ORDER BY t.conference_date, t.title, p.paragraph_number
        """
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        results = []
        for row in rows:
            matched_keywords = json.loads(row[4]) if row[4] else []
            
            # Find which keywords actually matched
            actual_matches = []
            content_lower = row[3].lower()
            for keyword in keywords:
                if keyword.lower() in content_lower:
                    actual_matches.append(keyword)
            
            results.append({
                'id': row[0],
                'talk_id': row[1],
                'paragraph_number': row[2],
                'content': row[3],
                'matched_keywords': actual_matches,
                'reviewed': bool(row[5]),
                'review_date': row[6],
                'talk_title': row[7],
                'speaker': row[8],
                'conference_date': row[9],
                'session': row[10],
                'hyperlink': row[11]
            })
        
        conn.close()
        return results
    
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
    
    def mark_paragraph_reviewed(self, paragraph_id: int, reviewed: bool = True):
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
    
    def get_talks_summary(self) -> List[Dict]:
        """Get summary of all talks"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                t.id, t.title, t.speaker, t.conference_date, t.session, t.hyperlink,
                COUNT(p.id) as paragraph_count,
                COUNT(CASE WHEN p.reviewed = 1 THEN 1 END) as reviewed_count
            FROM talks t
            LEFT JOIN paragraphs p ON t.id = p.talk_id
            GROUP BY t.id, t.title, t.speaker, t.conference_date, t.session, t.hyperlink
            ORDER BY t.conference_date DESC, t.title
        """)
        
        rows = cursor.fetchall()
        talks = []
        for row in rows:
            talks.append({
                'id': row[0],
                'title': row[1],
                'speaker': row[2],
                'conference_date': row[3],
                'session': row[4],
                'hyperlink': row[5],
                'paragraph_count': row[6],
                'reviewed_count': row[7]
            })
        
        conn.close()
        return talks
    
    def add_keywords(self, keywords: List[str]):
        """Add keywords to the keywords table"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for keyword in keywords:
            try:
                cursor.execute("INSERT INTO keywords (keyword) VALUES (?)", (keyword,))
            except sqlite3.IntegrityError:
                pass  # Keyword already exists
        
        conn.commit()
        conn.close()
    
    def get_keywords(self) -> List[str]:
        """Get all keywords"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT keyword FROM keywords ORDER BY keyword")
        rows = cursor.fetchall()
        
        conn.close()
        return [row[0] for row in rows]
    
    def delete_keyword(self, keyword: str):
        """Delete a keyword and all its associations"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get keyword ID
        cursor.execute("SELECT id FROM keywords WHERE keyword = ?", (keyword,))
        keyword_row = cursor.fetchone()
        
        if keyword_row:
            keyword_id = keyword_row[0]
            
            # Delete associations first
            cursor.execute("DELETE FROM paragraph_keywords WHERE keyword_id = ?", (keyword_id,))
            
            # Delete the keyword
            cursor.execute("DELETE FROM keywords WHERE id = ?", (keyword_id,))
            
            conn.commit()
        
        conn.close()
    
    def get_paragraphs_by_keyword(self, keyword: str) -> List[Dict]:
        """Get all paragraphs that match a specific keyword"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                p.id, p.talk_id, p.paragraph_number, p.content, 
                p.matched_keywords, p.reviewed, p.review_date,
                t.title, t.speaker, t.conference_date, t.session, t.hyperlink
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
            
            results.append({
                'id': row[0],
                'talk_id': row[1],
                'paragraph_number': row[2],
                'content': row[3],
                'matched_keywords': matched_keywords,
                'reviewed': bool(row[5]),
                'review_date': row[6],
                'talk_title': row[7],
                'speaker': row[8],
                'conference_date': row[9],
                'session': row[10],
                'hyperlink': row[11]
            })
        
        conn.close()
        return results
    
    def parse_talk_file(self, file_path: str) -> Dict:
        """Parse a single talk file and return its metadata and content"""
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        
        lines = content.split('\n')
        
        # Extract metadata from first 3 lines
        title = lines[0].replace('Title: ', '') if lines[0].startswith('Title: ') else ''
        speaker = lines[1].replace('Speaker: ', '') if lines[1].startswith('Speaker: ') else ''
        url = lines[2].replace('URL: ', '') if lines[2].startswith('URL: ') else ''
        
        # Extract talk body (skip metadata + blank line)
        talk_body = '\n'.join(lines[4:]) if len(lines) > 4 else ''
        
        # Extract year and month from file path
        path_parts = file_path.split(os.sep)
        year = path_parts[-3] if len(path_parts) >= 3 else ''
        month = path_parts[-2] if len(path_parts) >= 2 else ''
        
        # Convert month to conference date
        conference_date = f"{'April' if month == '04' else 'October'} {year}" if year and month else ''
        
        return {
            'title': title,
            'speaker': speaker,
            'url': url,
            'conference_date': conference_date,
            'session': None,  # Not available in file format
            'content': talk_body,
            'file_path': file_path
        }
    
    def split_into_paragraphs(self, content: str) -> List[str]:
        """Split talk content into paragraphs"""
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
    
    def scan_for_keywords(self, keywords: List[str], match_whole_words: bool = True) -> List[Dict]:
        """Scan all text files for keywords and return matching paragraphs"""
        results = []
        
        if not os.path.exists(self.data_path):
            return results
        
        # Precompile regex patterns if whole word matching
        patterns = None
        if match_whole_words:
            patterns = [re.compile(rf'\\b{re.escape(keyword)}\\b', re.IGNORECASE) for keyword in keywords]
        
        # Walk through the directory structure
        for root, dirs, files in os.walk(self.data_path):
            for file in files:
                if file.endswith('.txt'):
                    file_path = os.path.join(root, file)
                    
                    try:
                        talk_data = self.parse_talk_file(file_path)
                        paragraphs = self.split_into_paragraphs(talk_data['content'])
                        
                        # Check each paragraph for keywords
                        for para_num, paragraph in enumerate(paragraphs, 1):
                            matched_keywords = []
                            paragraph_lower = paragraph.lower()
                            
                            if match_whole_words:
                                for idx, pattern in enumerate(patterns):
                                    if pattern.search(paragraph):
                                        matched_keywords.append(keywords[idx])
                            else:
                                for keyword in keywords:
                                    if keyword.lower() in paragraph_lower:
                                        matched_keywords.append(keyword)
                            
                            if matched_keywords:
                                results.append({
                                    'talk_data': talk_data,
                                    'paragraph_number': para_num,
                                    'content': paragraph,
                                    'matched_keywords': matched_keywords
                                })
                    
                    except Exception as e:
                        print(f"Error processing file {file_path}: {e}")
                        continue
        
        return results

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
            # Add new talk
            cursor.execute("""
                INSERT INTO talks (title, speaker, conference_date, session, hyperlink)
                VALUES (?, ?, ?, ?, ?)
            """, (talk_data['title'], talk_data['speaker'], talk_data['conference_date'], 
                  talk_data['session'], talk_data['url']))
            talk_id = cursor.lastrowid
        
        conn.commit()
        conn.close()
        return talk_id
    
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
    
    def add_paragraph_keyword_associations(self, paragraph_id: int, keywords: List[str]):
        """Add keyword associations for a paragraph"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for keyword in keywords:
            # Get or create keyword ID
            cursor.execute("SELECT id FROM keywords WHERE keyword = ?", (keyword,))
            keyword_row = cursor.fetchone()
            
            if not keyword_row:
                cursor.execute("INSERT INTO keywords (keyword) VALUES (?)", (keyword,))
                keyword_id = cursor.lastrowid
            else:
                keyword_id = keyword_row[0]
            
            # Add association (ignore if already exists)
            try:
                cursor.execute("""
                    INSERT INTO paragraph_keywords (paragraph_id, keyword_id)
                    VALUES (?, ?)
                """, (paragraph_id, keyword_id))
            except sqlite3.IntegrityError:
                pass  # Association already exists
        
        conn.commit()
        conn.close()
    
    def search_and_populate_database(self, keywords: List[str], match_whole_words: bool = True) -> List[Dict]:
        """Search for keywords in files and populate database with matching content"""
        # Add keywords to database
        self.add_keywords(keywords)
        
        # Scan files for matches
        scan_results = self.scan_for_keywords(keywords, match_whole_words=match_whole_words)
        
        # Add matching content to database
        database_results = []
        for result in scan_results:
            talk_data = result['talk_data']
            
            # Add or update talk
            talk_id = self.add_or_update_talk(talk_data)
            
            # Add or update paragraph
            paragraph_id = self.add_or_update_paragraph(
                talk_id, 
                result['paragraph_number'], 
                result['content'], 
                result['matched_keywords']
            )
            
            # Add keyword associations
            self.add_paragraph_keyword_associations(paragraph_id, result['matched_keywords'])
            
            # Prepare result for return
            database_results.append({
                'id': paragraph_id,
                'talk_id': talk_id,
                'paragraph_number': result['paragraph_number'],
                'content': result['content'],
                'matched_keywords': result['matched_keywords'],
                'reviewed': False,
                'review_date': None,
                'talk_title': talk_data['title'],
                'speaker': talk_data['speaker'],
                'conference_date': talk_data['conference_date'],
                'session': talk_data['session'],
                'hyperlink': talk_data['url']
            })
        
        return database_results