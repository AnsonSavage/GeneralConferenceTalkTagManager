import sqlite3
import os

def explore_database():
    """Explore the database by printing the names/content of each table."""
    
    # Find the database file
    db_path = "talks_since_2007.db"
    db_path = db_path if os.path.exists(db_path) else None
    
    if not db_path:
        print("❌ Database file not found. Please check the path.")
        print("Looking for database files...")
        # List all .db files in parent directory
        parent_dir = ".."
        for file in os.listdir(parent_dir):
            if file.endswith('.db'):
                print(f"Found: {file}")
        return
    
    print(f"📁 Using database: {db_path}")
    print("=" * 50)
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get all table names
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        print(f"📊 Found {len(tables)} tables in the database:\n")
        
        for table_tuple in tables:
            table_name = table_tuple[0]
            print(f"🗂️  TABLE: {table_name}")
            print("-" * 30)
            
            # Get column information
            cursor.execute(f"PRAGMA table_info({table_name});")
            columns = cursor.fetchall()
            
            print("📋 Columns:")
            for col in columns:
                col_name = col[1]
                col_type = col[2]
                print(f"   • {col_name} ({col_type})")
            
            # Get row count
            cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
            row_count = cursor.fetchone()[0]
            print(f"📈 Total rows: {row_count}")
            
            # Show a few sample entries
            if row_count > 0:
                print("🔍 Sample entries:")
                cursor.execute(f"SELECT * FROM {table_name} LIMIT 3;")
                sample_rows = cursor.fetchall()
                
                for i, row in enumerate(sample_rows, 1):
                    print(f"   Row {i}: {row}")
            
            print("\n" + "=" * 50 + "\n")
        
        conn.close()
        
    except sqlite3.Error as e:
        print(f"❌ Database error: {e}")
    except Exception as e:
        print(f"❌ Error: {e}")

def explore_specific_table(table_name):
    """Explore a specific table in more detail."""
    
    # Find database (same logic as above)
    db_path = None
    possible_paths = [
        "../conference_talks.db",
        "../data/conference_talks.db", 
        "../database.db",
        "../talks.db"
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            db_path = path
            break
    
    if not db_path:
        print("❌ Database file not found.")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print(f"🔍 Detailed view of table: {table_name}")
        print("=" * 50)
        
        # Get all data from the table
        cursor.execute(f"SELECT * FROM {table_name};")
        rows = cursor.fetchall()
        
        # Get column names
        cursor.execute(f"PRAGMA table_info({table_name});")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        
        print(f"📋 Columns: {', '.join(column_names)}")
        print(f"📈 Total rows: {len(rows)}")
        print("-" * 50)
        
        # Print all rows (or first 20 if too many)
        max_rows = min(20, len(rows))
        for i, row in enumerate(rows[:max_rows]):
            print(f"Row {i+1}:")
            for col_name, value in zip(column_names, row):
                # Truncate long values for readability
                if isinstance(value, str) and len(value) > 100:
                    value = value[:100] + "..."
                print(f"   {col_name}: {value}")
            print()
        
        if len(rows) > max_rows:
            print(f"... and {len(rows) - max_rows} more rows")
        
        conn.close()
        
    except sqlite3.Error as e:
        print(f"❌ Database error: {e}")

if __name__ == "__main__":
    print("🗄️  DATABASE EXPLORER")
    print("=" * 50)
    
    # First, explore all tables
    explore_database()
    
    # Then ask if user wants to explore specific tables
    print("\n" + "🔍" * 20)
    print("Want to explore a specific table in detail?")
    print("Uncomment one of the lines below and run again:")
    print("# explore_specific_table('talks')")
    print("# explore_specific_table('paragraphs')")
    print("# explore_specific_table('tags')")
    print("# explore_specific_table('paragraph_tags')")