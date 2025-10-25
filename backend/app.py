from fastapi import FastAPI, HTTPException, Query, Path
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from recommender import get_recommendations
from database import supabase
from datetime import datetime
from models import HealthResponse, TagsResponse, UserResponse, CourseDetail, \
        RecommendationsResponse, SearchResponse
from helpers import get_course_details, get_user_profile, get_user_stats
from typing import Optional
from uuid import UUID

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events.
    This runs when the API starts up and shuts down.
    """
    try:
        # Test connection
        supabase.table('users').select('id').limit(1).execute()
        print("Supabase connected successfully")
        print("API is ready")
    except Exception as e:
        # If we can't connect to the database, there's no point in running
        print(f"Error connecting to Supabase: {e}")
        exit(1)
    yield


# Initialize FastAPI application with metadata
app = FastAPI(
    title="Course Recommendation API",
    description="AI-powered personalized course recommendations",
    version="1.0.0",
    docs_url="/docs",  # Swagger UI documentation
    redoc_url="/redoc",  # ReDoc documentation
    lifespan=lifespan
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/", tags=["Root"])
def root():
    """
    Helps verify the API is running.
    """
    return {
        "message": "Course Recommendation API",
        "version": "1.0.0",
        "documentation": "/docs",
    }

@app.get("/health", response_model=HealthResponse, tags=["Health"])
def health_check():
    """
    Health check endpoint for monitoring.
    Returns current status and timestamp.
    """
    return {
        "status": "healthy",
        "message": "Recommendation API is running",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/tags", response_model=TagsResponse, tags=["Tags"])
def get_tags():
    """
    Get all available tags for courses.
    Used for filtering and user interest selection.
    """
    try:
        # Fetch all tags from database, sorted alphabetically
        response = supabase.table('tags').select('name').order('name').execute()
        
        # Extract just the tag names into a simple list
        tags_list = [row['name'] for row in response.data]
        
        return {
            "tags": tags_list,
            "count": len(tags_list)
        }
    except Exception as e:
        # If anything goes wrong, return a 500 error with details
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/users/{user_id}", response_model=UserResponse, tags=["Users"])
def get_user(user_id: UUID = Path(description="The ID of the user")):
    """
    Get user profile and statistics.
    Returns user info, ratings, and course history.
    """
    try:
        # Fetch user's profile information
        profile = get_user_profile(user_id)
        if not profile:
            # User doesn't exist in our database
            raise HTTPException(status_code=404, detail=f"User {user_id} not found")

        # Get user's statistics (courses taken, ratings given, etc.)
        stats = get_user_stats(user_id)

        return {
            "profile": profile,
            "stats": stats
        }
    except HTTPException:
        # Re-raise HTTP exceptions (like 404) without wrapping them
        raise
    except Exception as e:
        # Catch any other errors and return 500
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/courses/{course_id}", response_model=CourseDetail, tags=["Courses"])
def get_course(course_id: str = Path(description="The ID of the course")):
    """
    Get detailed information about a specific course.
    Includes description, rating, tags, and reviews.
    """
    try:
        # Fetch complete course details
        details = get_course_details(course_id)
        if not details:
            # Course doesn't exist
            raise HTTPException(status_code=404, detail=f"Course {course_id} not found")

        return details
    except HTTPException:
        # Pass through HTTP exceptions
        raise
    except Exception as e:
        # Handle unexpected errors
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/recommendations/{user_id}", response_model=RecommendationsResponse, tags=["Recommendations"])
def get_user_recommendations(
    user_id: UUID = Path(description="The ID of the user"),
    tags: Optional[str] = Query(None, description="Comma-separated career tags", examples=["web-developer,devops-engineer"]),
    limit: int = Query(10, description="Number of recommendations", ge=1, le=20)
):
    """
    Get personalized course recommendations for a user.
    Uses hybrid collaborative + content-based filtering.
    
    Optionally filter by career path tags (e.g., "web-developer,data-scientist").
    """
    try:
        # First, make sure the user actually exists
        profile = get_user_profile(user_id)
        if not profile:
            raise HTTPException(status_code=404, detail=f"User {user_id} not found")

        # Parse comma-separated tags if provided
        desired_tags = None
        if tags:
            # Split by comma and strip whitespace, filter out empty strings
            desired_tags = [tag.strip() for tag in tags.split(',') if tag.strip()]

        # Call our recommendation engine
        # This is where collaborative + content filtering happens
        recs = get_recommendations(
            user_id=user_id,
            desired_tags=desired_tags,
            top_n=limit
        )

        # Handle case where we couldn't generate any recommendations
        if recs.empty:
            return {
                "user_id": user_id,
                "desired_tags": desired_tags,
                "count": 0,
                "recommendations": []
            }

        # Convert DataFrame to list of dictionaries for JSON response
        recommendations_list = []
        for _, row in recs.iterrows():
            recommendations_list.append({
                "course_id": row['course_id'],
                "name": row['name'],
                "url": row['source_url'],
                "description": row['description'],
                "score": round(float(row['final_score']), 2),  # Overall score
                "collaborative_score": round(float(row['collab_score']), 2),  # From similar users
                "content_score": round(float(row['content_score']), 2),  # From user's interests
                "confidence": row['confidence'],  # How confident we are in this recommendation
                "avg_rating": round(float(row['avg_rating']), 2) if row['avg_rating'] else 0,
                "tags": row['tags'] if isinstance(row['tags'], list) else [],
                "reasons": row['reasons'] if isinstance(row['reasons'], list) else []  # Human-readable explanations
            })

        return {
            "user_id": user_id,
            "desired_tags": desired_tags,
            "count": len(recommendations_list),
            "recommendations": recommendations_list
        }

    except HTTPException:
        # Let HTTP exceptions pass through
        raise
    except Exception as e:
        # Catch-all for unexpected errors
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/search/courses", response_model=SearchResponse, tags=["Search"])
def search_courses(
    q: Optional[str] = Query(None, description="Search query", examples=["database"]),
    tags: Optional[str] = Query(None, description="Filter by tags", examples=["backend"]),
    limit: int = Query(20, description="Number of results", ge=1, le=50)
):
    """
    Search for courses by keyword.
    Optionally filter by tags.
    
    This is a simple text search on course descriptions.
    For personalized recommendations, use the /recommendations endpoint instead.
    """
    try:
        # Start building the query
        query = supabase.table('courses').select('id, description, rating, name, source_url')
        
        # Add search filter if query provided
        if q:
            # Case-insensitive search in course descriptions
            query = query.ilike('description', f'%{q}%')
        
        # Limit the number of results
        query = query.limit(limit)
        
        # Execute the query
        courses_response = query.execute()
        
        # Build the response list
        courses = []
        for row in courses_response.data:
            # Get tags for each course
            tags_response = supabase.table('course_tag').select('tags(name)').eq('course_id', row['id']).execute()
            course_tags = [t['tags']['name'] for t in tags_response.data if t.get('tags')]
            
            courses.append({
                "id": row['id'],
                "description": row['description'],
                "name": row['name'],
                "url": row['source_url'],
                "rating": round(float(row['rating']), 2) if row['rating'] else 0,
                "tags": course_tags
            })

        return {
            "query": q,
            "tags_filter": tags.split(',') if tags else None,
            "count": len(courses),
            "courses": courses
        }

    except Exception as e:
        # Handle any errors
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    """
    Development server entry point.
    """
    import uvicorn
    uvicorn.run(
        "app:app", 
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info" 
    )