# CourseCompass - AI Course Recommendations for CS/IT Students

Stop spending 3 hours scrolling through the course catalog at 2am. Let AI do it for you.

---

# PART A: Project Responses

**Team:** TCP Turtles

**Members:**
- Tanni
- Mark
- Russell
- Karthik
- Arnav

---

## Project Scope

### A1: Problem Relevance

**The Problem:**

Look, choosing courses sucks. You've got hundreds of options, zero idea which ones are actually good, and your academic advisor is somehow always on leave. You end up in courses you hate because your friend's cousin said it was "easy" (it wasn't), or you miss out on great classes because nobody told you about them.

Specific pain points we're solving:
- You don't know if CS3005 is worth your time.
- You want to specialize in web dev but have no clue which electives actually help.
- Your friends took different courses so you can't even ask for advice.
- Rate My Professors doesn't exist for courses, only individual lecturers.

**Why This Matters:**

Picking the wrong courses means wasted tuition money, delayed graduation, and spending a semester learning COBOL when you wanted to learn React. Not great.

**Our Scope:**

We built a recommendation system that actually understands what you want:
- Analyzes your course history and ratings to figure out your preferences
- Finds students with similar tastes and shows you what they loved
- Matches courses to your interests (web dev, AI, cybersecurity, etc.)
- Filters by career goals so you're not just guessing
- Explains WHY it's recommending something (no black box nonsense)

**What We're NOT Doing (Yet):**
- Mobile app (it's a web app for now)
- Social features like course reviews and comments
- Automated degree planning (though we could totally add this)
- Integration with university enrollment systems

**Current Implementation:**
This is a proof of concept focused on Computer Science and IT programs. We're using mock course data, so don't actually use this to plan your real degree. But the algorithm works and could scale to real university data.

---

### A2: Project Desirability

**Tech Stack (aka "Will This Actually Work?"):**

**Frontend:** Next.js
**Backend:** FastAPI (Python) because pandas (they're cute)
**Database:** Supabase
**ML Stuff:** scikit-learn for the actual recommendation algorithms


**Risks & How We're Handling Them:**

1. **New User Problem**
   - Risk: Can't recommend courses if you haven't rated anything
   - Solution: Ask for interests during signup, use content-based filtering as fallback, show popular courses when we're totally clueless

2. **Not Enough Data**
   - Risk: 5 users don't make a useful recommendation system
   - Solution: Hybrid approach (collaborative + content-based), lowered rating thresholds to include more data, gracefully degrade to "just show popular stuff"

3. **Performance Dies With Scale**
   - Risk: Loading all user data every time = slow death
   - Solution: Built a caching system (5-10 min TTL), optimized database queries, precompute expensive stuff


**Development Timeline:**

What we've built:
- Database schema with users, courses, ratings, tags, history
- Auth system (Supabase handles the annoying parts)
- Collaborative filtering (finds similar users via cosine similarity)
- Content-based filtering (matches courses to your interests)
- Hybrid scoring that combines both approaches
- Caching layer so the app doesn't crawl
- Clean UI for browsing, rating, and viewing recommendations

What we could add:
- Prerequisite tracking for proper course sequencing
- Full degree plan generation (like a 4-year roadmap)
- More sophisticated ML (matrix factorization, neural networks if we're feeling ambitious)
- A/B testing to tune the algorithm
- Actually integrating with university systems

---

### A3: Target Users

**Who Actually Uses This:**

**Mark - The Undecided Second Year**
- Switched from Engineering to CS, has no idea what he's doing
- Wants to try different areas before specializing
- Needs courses that won't destroy his GPA while he figures things out
- Our system: Shows highly-rated intro courses in different CS areas, suggests based on what similar explorers enjoyed

**Russell - Web Dev Track Student**
- Knows he wants to build websites and apps
- Doesn't care about theory-heavy courses unless necessary
- Wants practical skills that look good on resumes
- Our system: Filters by "web-developer" tag, prioritizes courses with frameworks and practical projects

**Karthik - The Grad Student Speed Runner**
- Taking 6 courses per semester to finish fast
- Can't afford to pick wrong courses
- Needs guaranteed high-quality classes
- Our system: High confidence recommendations from similar power users, detailed ratings breakdown

**Why These Users:**

These are real students we know. The system works whether you're exploring, specializing, or just trying to survive. Undergrad, masters, doesn't matter - if you're picking CS/IT courses, this helps.

---

## Design Intentions (C1, C2)

### C1: User Interface

**Design Philosophy: Make It Not Ugly**

We went for clean and simple because nobody wants to navigate a cluttered mess when they're already stressed about course selection.

**Visual Stuff:**
- Used a consistent color scheme (white and red, good contrast for readability)
- Clean sans-serif fonts with clear hierarchy (big headings, readable body text)
- Card-based layout - each course is a card, easy to scan
- Consistent spacing so nothing feels cramped or weirdly spaced

**What We Improved:**
- Started with one massive signup form, split it into 3 steps so it's less overwhelming
- Changed from boring lists to card grids because visual hierarchy matters
- Made tag selection searchable instead of scrolling through 50 tags
- Added visual score indicators instead of just numbers

---

### C2: User Experience

**Making It Actually Usable:**

**Signup Flow:**
Three steps that don't suck:
1. Email and password (standard stuff)
2. Bio (optional, skip if you want)
3. Pick interests (searchable tags, pretty straightforward)

If you try to move forward with invalid data, we tell you what's wrong. No cryptic error messages.

**Navigation:**
- Top nav bar always visible with Courses, Recommendations, Profile
- Back buttons in multi-step flows
- You can always get home

**Feedback:**
- Buttons show loading spinners so you know something's happening
- Success messages when you rate a course or add to history
- Error messages that actually explain the problem
- Hover effects so you know what's clickable

**The Recommendation Flow:**
1. Click "Recommendations"
2. See loading skeleton (better than staring at blank screen)
3. Get personalized list with scores and explanations
4. Filter by career goal if you want
5. Click a course to see details
6. Rate it, system updates recommendations
7. Success message confirms you're good

**Accessibility:**
- Keyboard navigation works
- Color isn't the only way to distinguish things
- Focus indicators for keyboard users
- Semantic HTML for screen readers

Not perfect but better than most university websites (low bar, we know).

---

## Development Solutions (D2)

### Solution 1: Hybrid Recommendation Algorithm

**The Main Function: `get_recommendations()`**

This is where we actually generate recommendations. It's not just "show popular courses" - it combines multiple approaches.

**Time Complexity Analysis:**

Building user-item matrix: O(n × m) where n = users, m = courses
- Uses pandas pivot_table (optimized)
- Cached for 5 minutes so we don't recompute every time

Finding similar users: O(k × n) where k = similar users we want
- Cosine similarity with sklearn (uses numpy under the hood)
- Only compares against top 15 similar users, not everyone
- Also cached

Predicting ratings: O(k × c) where c = candidate courses
- Only looks at similar users × candidate courses
- Weighted average based on similarity scores

Overall: Fast enough with caching, would scale to thousands of users

**Code Structure:**

```python
def get_recommendations(user_id, desired_tags, top_n):
    # Load data (cached, so usually fast)
    courses = load_courses_data()
    history = load_user_history(user_id)
    
    # Filter out courses they've taken
    candidates = courses[~courses.in(history)]
    
    # Collaborative filtering - "students like you also liked..."
    collab_scores = predict_ratings_collaborative(user_id, candidates)
    
    # Content-based - "based on your interests..."
    content_scores = calculate_content_scores(user_id, candidates, desired_tags)
    
    # Combine both with weighted average (60% collaborative, 40% content)
    final_scores = combine_scores(collab_scores, content_scores)
    
    # Generate human-readable explanations
    recommendations = add_reasoning(final_scores)
    
    return recommendations
```

**Why This Design:**
- Each function does one thing (single responsibility)
- Easy to test each part independently
- Can swap out collaborative or content filtering without breaking everything
- Clear data flow from start to finish

**Integration:**
The FastAPI endpoints call this function, it calls the database layer, uses the caching module, and returns clean pandas DataFrames that are easy to work with.

---

### Solution 2: Caching for Performance

**The Problem:**

Without caching, every recommendation request loads ALL user ratings from the database. 10 concurrent users = 40+ database queries. Response time: 2.5 seconds. Database melts down.

**The Solution:**

Simple in-memory cache with time-to-live (TTL):

```python
class DataCache:
    def get(self, key, ttl_seconds=300):
        if key in cache and not_expired:
            return cached_data  # Fast
        return None  # Cache miss
    
    def set(self, key, value):
        cache[key] = value
        timestamp[key] = now()
```

**Cache Strategy:**
- Static stuff (courses, tags): 10 min TTL
- User data (ratings, history): 1 min TTL
- Expensive computations (similar users): 5 min TTL

**Results:**
- First request: 0.8s (loads from DB)
- Next requests: 0.15s (cache hit) - 5x faster
- 90% fewer database queries
- Handles 10+ concurrent users easily

**Scalability Path:**
1. Current: In-memory cache (works for demo)
2. Next: Redis for distributed cache (multiple servers)
3. Future: Precomputed recommendations (background jobs)

This shows we're thinking about scale, not just making a demo that barely works.

---

## Technologies Used (D3)

### Frontend
- **Next.js 14** - React framework with file-based routing
- **TypeScript** - Type safety so we catch bugs before runtime
- **Tailwind CSS** - Utility classes for styling
- **Supabase Client** - Auth and database from frontend

### Backend
- **FastAPI** - Python web framework with automatic API docs
- **Pandas** - Data manipulation
- **NumPy** - Math operations
- **scikit-learn** - Machine learning (cosine similarity)
- **Uvicorn** - ASGI server

### Database
- **Supabase (PostgreSQL)** - Managed database with auto-generated REST API
- **Supabase Auth** - Handles authentication, email confirmation, JWT tokens

---

# PART B: Setup and User Guide

## Installation

### What You Need
- Docker & Docker Compose installed

### ENV SETUP

USE ENV FILE PROVIDED IN ADDITIONAL FILES ON DEVPOST.
ADD IT TO PROJECT ROOT DIR.

### Run the containers
```bash
docker-compose up --build
```

### To stop the containers
```bash
docker-compose down
```

## How to Use It

**First Time:**
1. Go to localhost:3000
2. Click "Sign up"
3. Fill in email/password, optionally add bio, select interest tags
4. Confirm email (check inbox)
5. Login

**Adding Courses:**
1. Browse courses on main page
2. Click "Add to My Courses" to mark as taken
3. Click "Rate Course" to give 1-5 stars on lecturer, material, grading, enjoyment
4. Ratings improve future recommendations

**Getting Recommendations:**
1. Click "Recommendations" in nav
2. Wait a second while it computes
3. See personalized list with scores and explanations
4. Filter by career path if you want (web dev, ML, cybersecurity, etc.)
5. Click course to view details

**Understanding Scores:**
- **Final Score:** Overall recommendation strength (0-5)
- **Reasons:** Plain English explanations like "Students like you rated this 4.7 stars"

---

# PART C: References

## Libraries Used

**Frontend:**
- Next.js (nextjs.org) - MIT License
- Tailwind CSS (tailwindcss.com) - MIT License
- shadcn/ui (ui.shadcn.com) - MIT License

**Backend:**
- FastAPI (fastapi.tiangolo.com) - MIT License
- Pandas (pandas.pydata.org) - BSD License
- scikit-learn (scikit-learn.org) - BSD License

**Database:**
- Supabase (supabase.com) - Apache 2.0 License

## Algorithms

**Collaborative Filtering:**
Based on user-user similarity using cosine similarity. Standard approach in recommendation systems.

**Content-Based Filtering:**
Tag-based preference matching. Courses scored based on overlap with user interests.

**Hybrid System:**
Combines both approaches with weighted scoring (60% collaborative, 40% content).

## AI Assistance

Used Claude (Anthropic) for:
- Code review and debugging
- Documentation writing
- Optimization suggestions
- Comment generation

All core logic and algorithms written by the team. AI was a coding assistant, not a replacement for actual thinking.

---

## Future Ideas

**Stuff We Could Add:**
- Full degree planner (generate 4-year course plans)
- Prerequisite tracking and validation
- Course difficulty prediction based on your GPA and history
- Integration with university enrollment systems
- Social features (course reviews, study groups)
- Better ML models (matrix factorization, deep learning)
- Mobile app version

**Scaling Beyond Mock Data:**
- Currently focused on CS/IT programs with mock data
- Could expand to all university programs
- Would need real course data from university registrar
- Algorithm already designed to handle scale

---

**Project Demo:** [YouTube Link]
**Code:** [https://github.com/MortalFlame21/hackathon_tcp_turtles/]
**Live Demo:** [Deployed URL]

---