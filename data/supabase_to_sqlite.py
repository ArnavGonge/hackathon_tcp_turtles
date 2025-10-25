# supabase_to_sqlite.py
import sqlite3
from supabase import create_client, Client
import os
from dotenv import load_dotenv

load_dotenv('../env')

# Supabase credentials
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')

# SQLite database file
SQLITE_DB = "dummy.db"

# Initialize Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# =====================
# STEP 1: Create SQLite Schema
# =====================

def create_sqlite_schema(conn):
    """Create all tables in SQLite"""
    cursor = conn.cursor()
    
    print("Creating SQLite schema...")
    
    # Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            username VARCHAR(255) NOT NULL,
            bio TEXT,
            created_at TEXT
        )
    ''')
    
    # Programs table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS programs (
            id VARCHAR(50) PRIMARY KEY,
            name VARCHAR(255) NOT NULL
        )
    ''')
    
    # Semesters table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sems (
            name VARCHAR(50) PRIMARY KEY,
            date_start TEXT
        )
    ''')
    
    # Tags table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tags (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL
        )
    ''')
    
    # Courses table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS courses (
            id VARCHAR(50) PRIMARY KEY,
            description TEXT,
            rating REAL DEFAULT 0.0
        )
    ''')
    
    # Course tags
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS course_tag (
            course_id VARCHAR(50) NOT NULL,
            tag_id INTEGER NOT NULL,
            PRIMARY KEY (course_id, tag_id),
            FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE CASCADE,
            FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE
        )
    ''')
    
    # Courses offered in semesters
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS offered_in (
            course_id VARCHAR(50) NOT NULL,
            sem_name VARCHAR(50) NOT NULL,
            PRIMARY KEY (course_id, sem_name),
            FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE CASCADE,
            FOREIGN KEY (sem_name) REFERENCES sems(name) ON DELETE CASCADE
        )
    ''')
    
    # Course listings in programs
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS listings (
            prog_id VARCHAR(50) NOT NULL,
            course_id VARCHAR(50) NOT NULL,
            PRIMARY KEY (prog_id, course_id),
            FOREIGN KEY (prog_id) REFERENCES programs(id) ON DELETE CASCADE,
            FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE CASCADE
        )
    ''')
    
    # User ratings
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ratings (
            id INTEGER PRIMARY KEY,
            course_id VARCHAR(50) NOT NULL,
            user_id INTEGER NOT NULL,
            lecturer INTEGER CHECK (lecturer >= 1 AND lecturer <= 5),
            material INTEGER CHECK (material >= 1 AND material <= 5),
            grading INTEGER CHECK (grading >= 1 AND grading <= 5),
            joy INTEGER CHECK (joy >= 1 AND joy <= 5),
            created_at TEXT,
            UNIQUE(course_id, user_id),
            FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE CASCADE,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    ''')
    
    # Course prerequisites
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS prereqs (
            course_id VARCHAR(50) NOT NULL,
            prereq_id VARCHAR(50) NOT NULL,
            PRIMARY KEY (course_id, prereq_id),
            FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE CASCADE,
            FOREIGN KEY (prereq_id) REFERENCES courses(id) ON DELETE CASCADE
        )
    ''')
    
    # User history
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS history (
            user_id INTEGER NOT NULL,
            course_id VARCHAR(50) NOT NULL,
            PRIMARY KEY (user_id, course_id),
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE CASCADE
        )
    ''')
    
    # Create indexes
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_course_tag_course ON course_tag(course_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_course_tag_tag ON course_tag(tag_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_ratings_course ON ratings(course_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_ratings_user ON ratings(user_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_offered_in_sem ON offered_in(sem_name)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_listings_prog ON listings(prog_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_prereqs_prereq ON prereqs(prereq_id)')
    
    conn.commit()
    print("✓ Schema created")

# =====================
# STEP 2: Copy Data from Supabase
# =====================

def copy_table(conn, table_name, columns):
    """Generic function to copy a table from Supabase to SQLite"""
    print(f"\nCopying table: {table_name}")
    
    # Fetch all data from Supabase
    try:
        response = supabase.table(table_name).select('*').execute()
        data = response.data
    except Exception as e:
        print(f"  ✗ Error fetching from Supabase: {e}")
        return
    
    if not data:
        print(f"  ⚠ No data found in {table_name}")
        return
    
    print(f"  Found {len(data)} rows")
    
    # Insert into SQLite
    cursor = conn.cursor()
    
    placeholders = ', '.join(['?' for _ in columns])
    column_names = ', '.join(columns)
    
    sql = f"INSERT OR REPLACE INTO {table_name} ({column_names}) VALUES ({placeholders})"
    
    rows_inserted = 0
    for row in data:
        try:
            values = [row.get(col) for col in columns]
            cursor.execute(sql, values)
            rows_inserted += 1
        except Exception as e:
            print(f"  ✗ Error inserting row: {e}")
            print(f"    Row: {row}")
    
    conn.commit()
    print(f"  ✓ Inserted {rows_inserted} rows")

# =====================
# STEP 3: Main Migration
# =====================

def migrate():
    """Main migration function"""
    print("="*60)
    print("MIGRATING SUPABASE DATABASE TO SQLITE")
    print("="*60)
    
    # Connect to SQLite
    conn = sqlite3.connect(SQLITE_DB)
    print(f"\n✓ Connected to SQLite database: {SQLITE_DB}")
    
    # Create schema
    create_sqlite_schema(conn)
    
    # Copy tables in order (respecting foreign key constraints)
    print("\n" + "="*60)
    print("COPYING DATA")
    print("="*60)
    
    # 1. Independent tables first (no foreign keys)
    copy_table(conn, 'programs', ['id', 'name'])
    copy_table(conn, 'sems', ['name', 'date_start'])
    copy_table(conn, 'tags', ['id', 'name'])
    copy_table(conn, 'users', ['id', 'username', 'bio', 'created_at'])
    copy_table(conn, 'courses', ['id', 'description', 'rating'])
    
    # 2. Junction/relationship tables
    copy_table(conn, 'course_tag', ['course_id', 'tag_id'])
    copy_table(conn, 'offered_in', ['course_id', 'sem_name'])
    copy_table(conn, 'listings', ['prog_id', 'course_id'])
    copy_table(conn, 'prereqs', ['course_id', 'prereq_id'])
    
    # 3. Tables with foreign keys to multiple tables
    copy_table(conn, 'ratings', ['id', 'course_id', 'user_id', 'lecturer', 'material', 'grading', 'joy', 'created_at'])
    copy_table(conn, 'history', ['user_id', 'course_id'])
    
    # Close connection
    conn.close()
    
    print("\n" + "="*60)
    print("✓ MIGRATION COMPLETE!")
    print("="*60)
    print(f"\nSQLite database saved to: {SQLITE_DB}")
    print("\nYou can now use this database locally for development.")

# =====================
# STEP 4: Verify Migration
# =====================

def verify_migration():
    """Check that data was copied correctly"""
    print("\n" + "="*60)
    print("VERIFYING MIGRATION")
    print("="*60)
    
    conn = sqlite3.connect(SQLITE_DB)
    cursor = conn.cursor()
    
    tables = [
        'users', 'programs', 'sems', 'tags', 'courses',
        'course_tag', 'offered_in', 'listings', 'ratings', 
        'prereqs', 'history'
    ]
    
    print("\nRow counts:")
    for table in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        print(f"  {table:20s}: {count:5d} rows")
    
    # Sample queries
    print("\n" + "-"*60)
    print("Sample data verification:")
    print("-"*60)
    
    # Check courses with ratings
    cursor.execute("""
        SELECT c.id, c.description, c.rating, COUNT(r.id) as num_ratings
        FROM courses c
        LEFT JOIN ratings r ON c.id = r.course_id
        GROUP BY c.id
        LIMIT 5
    """)
    
    print("\nSample courses:")
    for row in cursor.fetchall():
        print(f"  {row[0]}: {row[1][:50]}... (Rating: {row[2]:.2f}, {row[3]} ratings)")
    
    # Check users with rating counts
    cursor.execute("""
        SELECT u.id, u.username, COUNT(r.id) as num_ratings
        FROM users u
        LEFT JOIN ratings r ON u.id = r.user_id
        GROUP BY u.id
        LIMIT 5
    """)
    
    print("\nSample users:")
    for row in cursor.fetchall():
        print(f"  User {row[0]} ({row[1]}): {row[2]} ratings")
    
    conn.close()
    print("\n✓ Verification complete")

# =====================
# RUN MIGRATION
# =====================

if __name__ == "__main__":
    try:
        migrate()
        verify_migration()
        
        print("\n" + "="*60)
        print("NEXT STEPS:")
        print("="*60)
        print("\n1. Your database is now available at: courses.db")
        print("2. You can query it with:")
        print("   import sqlite3")
        print("   conn = sqlite3.connect('courses.db')")
        print("   cursor = conn.cursor()")
        print("   cursor.execute('SELECT * FROM courses LIMIT 5')")
        print("\n3. Or use a SQLite browser: https://sqlitebrowser.org/")
        
    except Exception as e:
        print(f"\n✗ Error during migration: {e}")
        import traceback
        traceback.print_exc()