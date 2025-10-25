# intelligent_populate_sqlite.py
import os
import json
import time
import sqlite3
import random
from dotenv import load_dotenv
import google.generativeai as genai
from faker import Faker

# Load environment variables
load_dotenv()

# Initialize
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
model = genai.GenerativeModel('gemini-2.5-flash')
fake = Faker()

SQLITE_DB = "dummy.db"

# =====================
# Database Helper Functions
# =====================

def get_db():
    """Get database connection"""
    conn = sqlite3.connect(SQLITE_DB)
    conn.row_factory = sqlite3.Row
    return conn

# =====================
# STEP 1: Generate Career Path Tags
# =====================

def generate_career_tags():
    """Use Gemini to generate career-focused tags based on actual courses"""
    
    print("="*60)
    print("STEP 1: Generating Career Path Tags")
    print("="*60)
    
    # Get sample courses
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, description FROM courses")
    sample_courses = cursor.fetchall()
    conn.close()
    
    course_list = "\n".join([f"- {c['id']}: {c['description']}" for c in sample_courses])
    
    prompt = f"""
You are a career counselor for computer science/software engineering students.

Analyze these course descriptions and generate 15-20 career path tags that represent common tech career trajectories.

Sample courses:
{course_list}

Focus on these career path categories:
1. Development roles: backend, frontend, fullstack, mobile, game-dev
2. Infrastructure/ops: devops, cloud, platform-engineering, sre
3. Data roles: data-engineering, data-science, ml-engineer, ai-engineer
4. Specialized: security, embedded, systems-programming, web3
5. Cross-functional: product-engineering, technical-leadership

Return ONLY a JSON array of career path tags:
["backend", "frontend", "fullstack", "devops", "cloud", ...]

Keep tags lowercase with hyphens. Focus on CAREERS not technologies.
"""
    
    print("\n🤖 Asking Gemini to generate career path tags...")
    response = model.generate_content(prompt)
    
    try:
        text = response.text.strip()
        if text.startswith('```'):
            text = text.split('```')[1]
            if text.startswith('json'):
                text = text[4:]
        text = text.strip()
        
        tags = json.loads(text)
        print(f"\n✓ Generated {len(tags)} career path tags:")
        for i, tag in enumerate(tags, 1):
            print(f"  {i:2d}. {tag}")
        
        return tags
    except json.JSONDecodeError as e:
        print(f"✗ Error parsing JSON: {e}")
        print(f"Response was: {response.text}")
        # Fallback career tags
        return [
            "backend", "frontend", "fullstack", "mobile", "game-dev",
            "devops", "cloud", "platform-engineering", "sre",
            "data-engineering", "data-science", "ml-engineer", "ai-researcher",
            "security", "embedded", "systems-programming", "web3",
            "product-engineering", "technical-leadership"
        ]

# =====================
# STEP 2: Insert Tags
# =====================

def insert_tags(tag_names):
    """Insert career tags into database"""
    
    print("\n" + "="*60)
    print("STEP 2: Inserting Career Tags into Database")
    print("="*60)
    
    conn = get_db()
    cursor = conn.cursor()
    
    tag_map = {}
    
    for tag_name in tag_names:
        try:
            cursor.execute("INSERT INTO tags (name) VALUES (?)", (tag_name,))
            tag_id = cursor.lastrowid
            tag_map[tag_name] = tag_id
            print(f"  ✓ {tag_name} (ID: {tag_id})")
        except sqlite3.IntegrityError:
            # Tag exists, fetch it
            cursor.execute("SELECT id FROM tags WHERE name = ?", (tag_name,))
            row = cursor.fetchone()
            if row:
                tag_id = row[0]
                tag_map[tag_name] = tag_id
                print(f"  ⟳ {tag_name} (already exists, ID: {tag_id})")
    
    conn.commit()
    conn.close()
    
    return tag_map

# =====================
# STEP 3: Assign Career Tags to Courses
# =====================

def assign_tags_to_courses_batch(tag_map):
    """Use Gemini to assign career tags to courses"""
    
    print("\n" + "="*60)
    print("STEP 3: Assigning Career Tags to Courses")
    print("="*60)
    
    conn = get_db()
    cursor = conn.cursor()
    
    # Get all courses
    cursor.execute("SELECT id, description FROM courses")
    courses = cursor.fetchall()
    
    tag_names = list(tag_map.keys())
    batch_size = 15  # Process 15 courses at a time
    
    all_assignments = []
    
    for i in range(0, len(courses), batch_size):
        batch = courses[i:i+batch_size]
        
        print(f"\n📦 Processing batch {i//batch_size + 1}/{(len(courses)-1)//batch_size + 1} ({len(batch)} courses)...")
        
        # Prepare course info
        course_info = []
        for course in batch:
            course_info.append({
                'id': course['id'],
                'description': course['description']
            })
        
        prompt = f"""
You are an experienced software recruiter. For each course, assign 2-4 relevant CAREER PATH tags that indicate which career trajectories this course prepares students for.

Available career path tags:
{', '.join(tag_names)}

Courses:
{json.dumps(course_info, indent=2)}

Think about: "A student taking this course is likely interested in which career path?"

Return ONLY a JSON object mapping course IDs to arrays of career tags:
{{
  "COURSE_ID_1": ["backend", "fullstack"],
  "COURSE_ID_2": ["data-science", "ml-engineer"],
  ...
}}

Rules:
- Assign 2-4 career tags per course
- Only use tags from the provided list
- Choose careers this course directly prepares students for
- No explanations, just JSON
"""
        
        try:
            response = model.generate_content(prompt)
            
            # Parse response
            text = response.text.strip()
            if text.startswith('```'):
                text = text.split('```')[1]
                if text.startswith('json'):
                    text = text[4:]
            text = text.strip()
            
            assignments = json.loads(text)
            
            # Process assignments
            for course_id, assigned_tags in assignments.items():
                print(f"\n  {course_id}:")
                print(f"    Career paths: {', '.join(assigned_tags)}")
                
                for tag_name in assigned_tags:
                    if tag_name in tag_map:
                        all_assignments.append((course_id, tag_map[tag_name]))
            
            # Rate limiting
            time.sleep(2)
            
        except Exception as e:
            print(f"  ✗ Error processing batch: {e}")
            if 'response' in locals():
                print(f"  Response: {response.text}")
    
    # Insert all assignments
    print("\n" + "-"*60)
    print("Inserting tag assignments into database...")
    
    if all_assignments:
        try:
            cursor.executemany(
                "INSERT OR IGNORE INTO course_tag (course_id, tag_id) VALUES (?, ?)",
                all_assignments
            )
            conn.commit()
            print(f"✓ Inserted {len(all_assignments)} career tag assignments")
        except Exception as e:
            print(f"✗ Error inserting assignments: {e}")
    
    conn.close()
    return all_assignments

# =====================
# STEP 4: Generate Career-Based User Personas
# =====================

def generate_user_personas(tag_map):
    """Create user personas based on career interests"""
    
    print("\n" + "="*60)
    print("STEP 4: Generating Career-Based User Personas")
    print("="*60)
    
    tag_names = list(tag_map.keys())
    
    prompt = f"""
Create 12 diverse student personas for a computer science program. Each persona represents a student interested in a specific career path.

Available career paths:
{', '.join(tag_names)}

For each persona, provide:
- type: Career interest (e.g., "Backend Engineer", "ML Engineer")
- career_tags: 2-3 career paths they're interested in (from the list)
- rating_style: How they rate courses ("generous": 4-5 stars, "balanced": 3-4 stars, "critical": 2-4 stars)

Return as JSON array:
[
  {{
    "type": "Backend Engineer",
    "career_tags": ["backend", "fullstack", "devops"],
    "rating_style": "balanced"
  }},
  ...
]
"""
    
    print("\n🎭 Creating user personas...")
    
    try:
        response = model.generate_content(prompt)
        text = response.text.strip()
        if text.startswith('```'):
            text = text.split('```')[1]
            if text.startswith('json'):
                text = text[4:]
        text = text.strip()
        
        personas = json.loads(text)
        print(f"✓ Generated {len(personas)} personas:")
        for p in personas:
            print(f"  - {p['type']}: interested in {', '.join(p['career_tags'])}")
        
        return personas
    except Exception as e:
        print(f"✗ Error generating personas: {e}")
        # Fallback personas
        return [
            {"type": "Backend Engineer", "career_tags": ["backend", "devops"], "rating_style": "balanced"},
            {"type": "Frontend Developer", "career_tags": ["frontend", "fullstack"], "rating_style": "generous"},
            {"type": "Data Scientist", "career_tags": ["data-science", "ml-engineer"], "rating_style": "critical"},
            {"type": "DevOps Engineer", "career_tags": ["devops", "cloud", "sre"], "rating_style": "balanced"},
            {"type": "Full Stack Dev", "career_tags": ["fullstack", "backend", "frontend"], "rating_style": "generous"},
            {"type": "ML Engineer", "career_tags": ["ml-engineer", "ai-researcher"], "rating_style": "critical"},
            {"type": "Mobile Dev", "career_tags": ["mobile", "frontend"], "rating_style": "balanced"},
            {"type": "Security Engineer", "career_tags": ["security", "backend"], "rating_style": "critical"},
            {"type": "Cloud Architect", "career_tags": ["cloud", "devops", "platform-engineering"], "rating_style": "balanced"},
            {"type": "Product Engineer", "career_tags": ["product-engineering", "fullstack"], "rating_style": "generous"}
        ]

# =====================
# STEP 5: Generate Realistic Ratings
# =====================

def generate_realistic_ratings(personas, tag_map):
    """Generate ratings based on career interests"""
    
    print("\n" + "="*60)
    print("STEP 5: Generating Career-Based Ratings")
    print("="*60)
    
    conn = get_db()
    cursor = conn.cursor()
    
    # Get all users
    cursor.execute("SELECT id, username FROM users")
    users = cursor.fetchall()
    
    # Get all courses with their career tags
    cursor.execute("SELECT id, description FROM courses")
    courses = cursor.fetchall()
    
    # Build course -> career tags mapping
    course_careers = {}
    for course in courses:
        cursor.execute("""
            SELECT t.name 
            FROM tags t
            JOIN course_tag ct ON t.id = ct.tag_id
            WHERE ct.course_id = ?
        """, (course['id'],))
        tags = [row[0] for row in cursor.fetchall()]
        course_careers[course['id']] = tags
    
    print(f"\n📊 Generating ratings for {len(users)} users...")
    
    ratings = []
    
    for user in users:
        # Assign random persona to user
        persona = random.choice(personas)
        user_id = user['id']
        
        print(f"\n  User {user_id} ({user['username']}): {persona['type']}")
        print(f"    Interested in: {', '.join(persona['career_tags'])}")
        
        # Rate 5-15 random courses
        num_ratings = random.randint(5, 15)
        courses_to_rate = random.sample(list(courses), min(num_ratings, len(courses)))
        
        rated_count = 0
        
        for course in courses_to_rate:
            course_id = course['id']
            career_tags = course_careers.get(course_id, [])
            
            # Calculate match between user interests and course careers
            matching_careers = set(career_tags) & set(persona['career_tags'])
            match_score = len(matching_careers)
            
            # Base rating depends on rating style
            if persona['rating_style'] == 'generous':
                base = 3.5 + match_score * 0.5
            elif persona['rating_style'] == 'balanced':
                base = 2.5 + match_score * 0.7
            else:  # critical
                base = 2.0 + match_score * 0.8
            
            # Add randomness
            base += random.uniform(-0.5, 0.8)
            base = max(1, min(5, base))
            
            # Generate individual ratings
            lecturer = max(1, min(5, int(base + random.uniform(-1, 1))))
            material = max(1, min(5, int(base + random.uniform(-1, 1))))
            grading = max(1, min(5, int(base + random.uniform(-1, 1))))
            joy = max(1, min(5, int(base + random.uniform(-1, 1))))
            
            ratings.append((course_id, user_id, lecturer, material, grading, joy))
            rated_count += 1
        
        print(f"    Rated {rated_count} courses")
    
    # Insert ratings
    print(f"\n💾 Inserting {len(ratings)} ratings into database...")
    
    try:
        cursor.executemany(
            "INSERT OR IGNORE INTO ratings (course_id, user_id, lecturer, material, grading, joy) VALUES (?, ?, ?, ?, ?, ?)",
            ratings
        )
        conn.commit()
        print(f"✓ Inserted {cursor.rowcount} ratings")
    except Exception as e:
        print(f"✗ Error inserting ratings: {e}")
    
    conn.close()
    return ratings

# =====================
# STEP 6: Update Statistics
# =====================

def update_course_ratings():
    """Calculate and update average ratings for courses"""
    
    print("\n" + "="*60)
    print("STEP 6: Updating Course Statistics")
    print("="*60)
    
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("SELECT id FROM courses")
    courses = cursor.fetchall()
    
    for course in courses:
        course_id = course['id']
        
        # Calculate average rating
        cursor.execute("""
            SELECT AVG((lecturer + material + grading + joy) / 4.0) as avg_rating,
                   COUNT(*) as count
            FROM ratings
            WHERE course_id = ?
        """, (course_id,))
        
        result = cursor.fetchone()
        
        if result['count'] > 0:
            avg_rating = result['avg_rating']
            cursor.execute(
                "UPDATE courses SET rating = ? WHERE id = ?",
                (avg_rating, course_id)
            )
            print(f"  ✓ {course_id}: {avg_rating:.2f} ⭐ ({result['count']} ratings)")
    
    conn.commit()
    conn.close()

def create_user_history():
    """Create history from ratings"""
    
    print("\n" + "="*60)
    print("STEP 7: Creating User History")
    print("="*60)
    
    conn = get_db()
    cursor = conn.cursor()
    
    # Copy from ratings to history
    cursor.execute("""
        INSERT OR IGNORE INTO history (user_id, course_id)
        SELECT DISTINCT user_id, course_id FROM ratings
    """)
    
    conn.commit()
    count = cursor.rowcount
    print(f"✓ Created {count} history records")
    
    conn.close()

# =====================
# STEP 7: Create Users if Needed
# =====================

def create_users_if_needed(num_users=50):
    """Create dummy users if table is empty"""
    
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) as count FROM users")
    user_count = cursor.fetchone()['count']
    
    if user_count == 0:
        print(f"\n👥 Creating {num_users} dummy users...")
        
        users = []
        for i in range(num_users):
            users.append((
                fake.user_name() + str(random.randint(100, 999)),
                fake.sentence() if random.random() > 0.5 else None
            ))
        
        cursor.executemany(
            "INSERT INTO users (username, bio) VALUES (?, ?)",
            users
        )
        conn.commit()
        print(f"  ✓ Created {num_users} users")
    else:
        print(f"\n👥 Found {user_count} existing users")
    
    conn.close()

# =====================
# MAIN EXECUTION
# =====================

def main():
    print("="*60)
    print("INTELLIGENT CAREER-BASED DATABASE POPULATION")
    print("="*60)
    
    # Check database exists
    if not os.path.exists(SQLITE_DB):
        print(f"\n✗ Database file '{SQLITE_DB}' not found!")
        print("Please run the migration script first.")
        return
    
    # Check courses exist
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) as count FROM courses")
    course_count = cursor.fetchone()['count']
    conn.close()
    
    if course_count == 0:
        print("\n⚠️  No courses found in database!")
        print("Please populate the courses table first.")
        return
    
    print(f"\n📚 Found {course_count} courses in database")
    
    # Create users if needed
    create_users_if_needed(num_users=50)
    
    # Generate career path tags
    career_tags = generate_career_tags()
    
    # Insert tags
    tag_map = insert_tags(career_tags)
    
    # Assign tags to courses
    assign_tags_to_courses_batch(tag_map)
    
    # Generate personas
    personas = generate_user_personas(tag_map)
    
    # Generate ratings
    generate_realistic_ratings(personas, tag_map)
    
    # Update statistics
    update_course_ratings()
    
    # Create history
    create_user_history()
    
    print("\n" + "="*60)
    print("✓ INTELLIGENT POPULATION COMPLETE!")
    print("="*60)
    print("\n🎉 Your database now has:")
    print("  - Career-focused tags (backend, frontend, devops, etc.)")
    print("  - Courses tagged with relevant career paths")
    print("  - Users with career interests")
    print("  - Realistic ratings based on career alignment")
    print("\n✨ Ready to build your recommendation system!")

if __name__ == "__main__":
    main()