# improve_data_density.py
import sqlite3
import random
from datetime import datetime, timedelta

SQLITE_DB = "dummy.db"

def get_db():
    conn = sqlite3.connect(SQLITE_DB)
    conn.row_factory = sqlite3.Row
    return conn

# =====================
# STEP 1: Populate Semesters
# =====================

def populate_semesters():
    """Create realistic semester records"""
    
    print("="*60)
    print("STEP 1: Populating Semesters")
    print("="*60)
    
    conn = get_db()
    cursor = conn.cursor()
    
    # Create semesters from 2024 to 2025
    semesters = [
        ('Semester 2 2024', '2024-07-22'),
        ('Semester 1 2025', '2025-02-24'),
        ('Semester 2 2025', '2025-07-24'),
    ]
    
    for sem_name, date_start in semesters:
        try:
            cursor.execute(
                "INSERT OR IGNORE INTO sems (name, date_start) VALUES (?, ?)",
                (sem_name, date_start)
            )
            print(f"  ✓ {sem_name}")
        except Exception as e:
            print(f"  ✗ {sem_name}: {e}")
    
    conn.commit()
    conn.close()
    
    return [s[0] for s in semesters]

# =====================
# STEP 2: Assign Courses to Semesters
# =====================

def assign_courses_to_semesters(semester_names):
    """Assign each course to 1-3 semesters (realistic offering pattern)"""
    
    print("\n" + "="*60)
    print("STEP 2: Assigning Courses to Semesters")
    print("="*60)
    
    conn = get_db()
    cursor = conn.cursor()
    
    # Get all courses
    cursor.execute("SELECT id FROM courses")
    courses = cursor.fetchall()
    
    offerings = []
    
    for course in courses:
        course_id = course['id']
        
        # Each course offered in 1-3 semesters (realistic)
        num_offerings = random.randint(1, 3)
        selected_sems = random.sample(semester_names, num_offerings)
        
        for sem in selected_sems:
            offerings.append((course_id, sem))
    
    # Insert offerings
    try:
        cursor.executemany(
            "INSERT OR IGNORE INTO offered_in (course_id, sem_name) VALUES (?, ?)",
            offerings
        )
        conn.commit()
        print(f"✓ Created {len(offerings)} course offerings")
        print(f"  Each course offered in ~{len(offerings) / len(courses):.1f} semesters on average")
    except Exception as e:
        print(f"✗ Error: {e}")
    
    conn.close()

# =====================
# STEP 3: Rebuild History Table (More Realistic)
# =====================

def rebuild_history_table():
    """
    Create realistic course history:
    - Each user has taken 8-20 courses
    - Courses follow prerequisite constraints (basic)
    - Mix of courses from different years
    """
    
    print("\n" + "="*60)
    print("STEP 3: Rebuilding History Table")
    print("="*60)
    
    conn = get_db()
    cursor = conn.cursor()
    
    # Clear existing history
    cursor.execute("DELETE FROM history")
    
    # Get all users
    cursor.execute("SELECT id FROM users")
    users = cursor.fetchall()
    
    # Get all courses
    cursor.execute("SELECT id FROM courses")
    all_courses = [c['id'] for c in cursor.fetchall()]
    
    # Get user personas (career interests from tags)
    cursor.execute("""
        SELECT DISTINCT user_id, t.name as career_tag
        FROM ratings r
        JOIN course_tag ct ON r.course_id = ct.course_id
        JOIN tags t ON ct.tag_id = t.id
        WHERE r.lecturer + r.material + r.grading + r.joy >= 16
        GROUP BY user_id, t.name
    """)
    user_interests = {}
    for row in cursor.fetchall():
        uid = row['user_id']
        if uid not in user_interests:
            user_interests[uid] = []
        user_interests[uid].append(row['career_tag'])
    
    print(f"\n📚 Building course history for {len(users)} users...")
    
    history_records = []
    
    for user in users:
        user_id = user['id']
        
        # Each user takes 8-20 courses (realistic for mid-program)
        num_courses = random.randint(8, 20)
        
        # Get user's career interests
        interests = user_interests.get(user_id, [])
        
        # Select courses
        if interests:
            # Prefer courses matching user interests
            cursor.execute("""
                SELECT DISTINCT c.id
                FROM courses c
                JOIN course_tag ct ON c.id = ct.course_id
                JOIN tags t ON ct.tag_id = t.id
                WHERE t.name IN ({})
            """.format(','.join(['?'] * len(interests))), interests)
            
            interested_courses = [row['id'] for row in cursor.fetchall()]
            
            # Take mostly interested courses, some random
            num_interested = int(num_courses * 0.7)  # 70% match interests
            num_random = num_courses - num_interested
            
            selected_courses = []
            if len(interested_courses) >= num_interested:
                selected_courses.extend(random.sample(interested_courses, num_interested))
            else:
                selected_courses.extend(interested_courses)
            
            # Fill remaining with random courses
            remaining = [c for c in all_courses if c not in selected_courses]
            if remaining:
                selected_courses.extend(random.sample(remaining, min(num_random, len(remaining))))
        else:
            # No interests, random selection
            selected_courses = random.sample(all_courses, min(num_courses, len(all_courses)))
        
        # Add to history
        for course_id in selected_courses:
            history_records.append((user_id, course_id))
        
        print(f"  User {user_id}: {len(selected_courses)} courses")
    
    # Insert into history
    cursor.executemany(
        "INSERT OR IGNORE INTO history (user_id, course_id) VALUES (?, ?)",
        history_records
    )
    conn.commit()
    
    print(f"\n✓ Created {len(history_records)} history records")
    print(f"  Average: {len(history_records) / len(users):.1f} courses per user")
    
    conn.close()

# =====================
# STEP 4: Align Ratings with History
# =====================

def align_ratings_with_history():
    """
    Ensure ratings are consistent with history:
    - Users can only rate courses they've taken
    - Add more ratings for courses in history
    """
    
    print("\n" + "="*60)
    print("STEP 4: Aligning Ratings with History")
    print("="*60)
    
    conn = get_db()
    cursor = conn.cursor()
    
    # Get user personas
    cursor.execute("SELECT id FROM users")
    users = cursor.fetchall()
    
    # Get course career tags
    cursor.execute("""
        SELECT c.id, GROUP_CONCAT(t.name) as tags
        FROM courses c
        JOIN course_tag ct ON c.id = ct.course_id
        JOIN tags t ON ct.tag_id = t.id
        GROUP BY c.id
    """)
    course_tags = {row['id']: row['tags'].split(',') if row['tags'] else [] for row in cursor.fetchall()}
    
    # Delete ratings for courses not in history
    cursor.execute("""
        DELETE FROM ratings
        WHERE NOT EXISTS (
            SELECT 1 FROM history h
            WHERE h.user_id = ratings.user_id
            AND h.course_id = ratings.course_id
        )
    """)
    deleted = cursor.rowcount
    print(f"  ✗ Removed {deleted} ratings for courses not in history")
    
    # Add ratings for courses in history that aren't rated yet
    cursor.execute("""
        SELECT h.user_id, h.course_id
        FROM history h
        LEFT JOIN ratings r ON h.user_id = r.user_id AND h.course_id = r.course_id
        WHERE r.id IS NULL
    """)
    
    missing_ratings = cursor.fetchall()
    print(f"  Found {len(missing_ratings)} courses in history without ratings")
    
    # Generate ratings for these courses
    new_ratings = []
    
    # Get user interests
    cursor.execute("""
        SELECT user_id, t.name as tag, AVG((lecturer + material + grading + joy) / 4.0) as avg_rating
        FROM ratings r
        JOIN course_tag ct ON r.course_id = ct.course_id
        JOIN tags t ON ct.tag_id = t.id
        GROUP BY user_id, t.name
    """)
    
    user_tag_preferences = {}
    for row in cursor.fetchall():
        uid = row['user_id']
        if uid not in user_tag_preferences:
            user_tag_preferences[uid] = {}
        user_tag_preferences[uid][row['tag']] = row['avg_rating']
    
    for record in missing_ratings:
        user_id = record['user_id']
        course_id = record['course_id']
        
        # Get course tags
        tags = course_tags.get(course_id, [])
        
        # Calculate expected rating based on user preferences
        user_prefs = user_tag_preferences.get(user_id, {})
        
        if user_prefs and tags:
            # Average of user's ratings for matching tags
            matching_ratings = [user_prefs[tag] for tag in tags if tag in user_prefs]
            if matching_ratings:
                base = sum(matching_ratings) / len(matching_ratings)
            else:
                base = 3.5  # Default
        else:
            base = 3.5  # Default
        
        # Add randomness
        base += random.uniform(-0.5, 0.5)
        base = max(1.5, min(5, base))
        
        # Generate individual ratings
        lecturer = max(1, min(5, int(base + random.uniform(-1, 1))))
        material = max(1, min(5, int(base + random.uniform(-1, 1))))
        grading = max(1, min(5, int(base + random.uniform(-1, 1))))
        joy = max(1, min(5, int(base + random.uniform(-1, 1))))
        
        new_ratings.append((course_id, user_id, lecturer, material, grading, joy))
    
    # Insert new ratings
    if new_ratings:
        cursor.executemany(
            "INSERT INTO ratings (course_id, user_id, lecturer, material, grading, joy) VALUES (?, ?, ?, ?, ?, ?)",
            new_ratings
        )
        conn.commit()
        print(f"  ✓ Added {len(new_ratings)} new ratings")
    
    conn.close()

# =====================
# STEP 5: Update Course Statistics
# =====================

def update_course_statistics():
    """Recalculate course average ratings"""
    
    print("\n" + "="*60)
    print("STEP 5: Updating Course Statistics")
    print("="*60)
    
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("""
        UPDATE courses
        SET rating = (
            SELECT AVG((lecturer + material + grading + joy) / 4.0)
            FROM ratings
            WHERE ratings.course_id = courses.id
        )
        WHERE EXISTS (
            SELECT 1 FROM ratings WHERE ratings.course_id = courses.id
        )
    """)
    
    updated = cursor.rowcount
    conn.commit()
    
    print(f"✓ Updated ratings for {updated} courses")
    
    conn.close()

# =====================
# STEP 6: Verify Data Quality
# =====================

def verify_data_quality():
    """Check that data is realistic and consistent"""
    
    print("\n" + "="*60)
    print("STEP 6: Verifying Data Quality")
    print("="*60)
    
    conn = get_db()
    cursor = conn.cursor()
    
    # Check 1: Users per course in history
    cursor.execute("""
        SELECT 
            MIN(course_count) as min_courses,
            AVG(course_count) as avg_courses,
            MAX(course_count) as max_courses
        FROM (
            SELECT user_id, COUNT(*) as course_count
            FROM history
            GROUP BY user_id
        )
    """)
    result = cursor.fetchone()
    print(f"\n📚 Courses per user:")
    print(f"  Min: {result['min_courses']}")
    print(f"  Avg: {result['avg_courses']:.1f}")
    print(f"  Max: {result['max_courses']}")
    
    # Check 2: Ratings per user
    cursor.execute("""
        SELECT 
            MIN(rating_count) as min_ratings,
            AVG(rating_count) as avg_ratings,
            MAX(rating_count) as max_ratings
        FROM (
            SELECT user_id, COUNT(*) as rating_count
            FROM ratings
            GROUP BY user_id
        )
    """)
    result = cursor.fetchone()
    print(f"\n⭐ Ratings per user:")
    print(f"  Min: {result['min_ratings']}")
    print(f"  Avg: {result['avg_ratings']:.1f}")
    print(f"  Max: {result['max_ratings']}")
    
    # Check 3: Rating distribution
    cursor.execute("""
        SELECT 
            AVG((lecturer + material + grading + joy) / 4.0) as overall_avg,
            COUNT(*) as total_ratings
        FROM ratings
    """)
    result = cursor.fetchone()
    print(f"\n🎯 Rating statistics:")
    print(f"  Total ratings: {result['total_ratings']}")
    print(f"  Average rating: {result['overall_avg']:.2f}")
    
    # Check 4: Consistency check
    cursor.execute("""
        SELECT COUNT(*) as inconsistent
        FROM ratings r
        WHERE NOT EXISTS (
            SELECT 1 FROM history h
            WHERE h.user_id = r.user_id AND h.course_id = r.course_id
        )
    """)
    result = cursor.fetchone()
    print(f"\n✓ Consistency check:")
    print(f"  Ratings without history: {result['inconsistent']} (should be 0)")
    
    # Check 5: Courses per semester
    cursor.execute("""
        SELECT sem_name, COUNT(*) as course_count
        FROM offered_in
        GROUP BY sem_name
        ORDER BY sem_name
    """)
    print(f"\n📅 Courses per semester:")
    for row in cursor.fetchall():
        print(f"  {row['sem_name']}: {row['course_count']} courses")
    
    # Check 6: Sample user history
    cursor.execute("""
        SELECT u.id, u.username, COUNT(h.course_id) as courses_taken, COUNT(r.id) as courses_rated
        FROM users u
        LEFT JOIN history h ON u.id = h.user_id
        LEFT JOIN ratings r ON u.id = r.user_id
        GROUP BY u.id
        LIMIT 5
    """)
    print(f"\n👤 Sample users:")
    for row in cursor.fetchall():
        print(f"  User {row['id']} ({row['username']}): {row['courses_taken']} courses, {row['courses_rated']} rated")
    
    conn.close()

# =====================
# MAIN EXECUTION
# =====================

def main():
    print("="*60)
    print("IMPROVING DATA DENSITY & CONSISTENCY")
    print("="*60)
    
    # Step 1: Populate semesters
    semester_names = populate_semesters()
    
    # Step 2: Assign courses to semesters
    assign_courses_to_semesters(semester_names)
    
    # Step 3: Rebuild history with realistic data
    rebuild_history_table()
    
    # Step 4: Align ratings with history
    align_ratings_with_history()
    
    # Step 5: Update course statistics
    update_course_statistics()
    
    # Step 6: Verify data quality
    verify_data_quality()
    
    print("\n" + "="*60)
    print("✓ DATA IMPROVEMENT COMPLETE!")
    print("="*60)
    print("\n✨ Your database now has:")
    print("  - Realistic course history (8-20 courses per user)")
    print("  - Consistent ratings (only for courses taken)")
    print("  - Populated semesters and course offerings")
    print("  - Dense, high-quality data for recommendations")
    print("\n🚀 Ready to build the recommendation system!")

if __name__ == "__main__":
    main()