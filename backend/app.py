# app.py
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
    try:
        # Test connection
        supabase.table('users').select('id').limit(1).execute()
        print("Supabase connected successfully")
        print("API is ready")
    except Exception as e:
        print(f"Error connecting to Supabase: {e}")
        exit(1)
    yield

app = FastAPI(
    title="Course Recommendation API",
    description="AI-powered personalized course recommendations",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/", tags=["Root"])
def root():
    return {
        "message": "Course Recommendation API",
        "version": "1.0.0",
        "documentation": "/docs",
    }

@app.get("/health", response_model=HealthResponse, tags=["Health"])
def health_check():
    return {
        "status": "healthy",
        "message": "Recommendation API is running",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/tags", response_model=TagsResponse, tags=["Tags"])
def get_tags():
    try:
        response = supabase.table('tags').select('name').order('name').execute()
        tags_list = [row['name'] for row in response.data]
        return {
            "tags": tags_list,
            "count": len(tags_list)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/users/{user_id}", response_model=UserResponse, tags=["Users"])
def get_user(user_id: UUID = Path(description="The ID of the user")):
    try:
        profile = get_user_profile(user_id)
        if not profile:
            raise HTTPException(status_code=404, detail=f"User {user_id} not found")

        stats = get_user_stats(user_id)

        return {
            "profile": profile,
            "stats": stats
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/courses/{course_id}", response_model=CourseDetail, tags=["Courses"])
def get_course(course_id: str = Path(description="The ID of the course")):
    try:
        details = get_course_details(course_id)
        if not details:
            raise HTTPException(status_code=404, detail=f"Course {course_id} not found")

        return details
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/recommendations/{user_id}", response_model=RecommendationsResponse, tags=["Recommendations"])
def get_user_recommendations(
    user_id: UUID = Path(description="The ID of the user"),
    tags: Optional[str] = Query(None, description="Comma-separated career tags", examples=["web-developer,devops-engineer"]),
    limit: int = Query(10, description="Number of recommendations", ge=1, le=20)
):
    try:
        profile = get_user_profile(user_id)
        if not profile:
            raise HTTPException(status_code=404, detail=f"User {user_id} not found")

        desired_tags = None
        if tags:
            desired_tags = [tag.strip() for tag in tags.split(',') if tag.strip()]

        recs = get_recommendations(
            user_id=user_id,
            desired_tags=desired_tags,
            top_n=limit
        )

        if recs.empty:
            return {
                "user_id": user_id,
                "desired_tags": desired_tags,
                "count": 0,
                "recommendations": []
            }

        recommendations_list = []
        for _, row in recs.iterrows():
            recommendations_list.append({
                "course_id": row['course_id'],
                "name": row['name'],
                "url": row['source_url'],
                "description": row['description'],
                "score": round(float(row['final_score']), 2),
                "collaborative_score": round(float(row['collab_score']), 2),
                "content_score": round(float(row['content_score']), 2),
                "confidence": row['confidence'],
                "avg_rating": round(float(row['avg_rating']), 2) if row['avg_rating'] else 0,
                "tags": row['tags'] if isinstance(row['tags'], list) else [],
                "reasons": row['reasons'] if isinstance(row['reasons'], list) else []
            })

        return {
            "user_id": user_id,
            "desired_tags": desired_tags,
            "count": len(recommendations_list),
            "recommendations": recommendations_list
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/search/courses", response_model=SearchResponse, tags=["Search"])
def search_courses(
    q: Optional[str] = Query(None, description="Search query", examples=["database"]),
    tags: Optional[str] = Query(None, description="Filter by tags", examples=["backend"]),
    limit: int = Query(20, description="Number of results", ge=1, le=50)
):
    try:
        query = supabase.table('courses').select('id, description, rating, name, source_url')
        
        if q:
            query = query.ilike('description', f'%{q}%')
        
        query = query.limit(limit)
        
        courses_response = query.execute()
        
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
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True, log_level="info")