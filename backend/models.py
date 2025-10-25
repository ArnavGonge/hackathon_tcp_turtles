from pydantic import BaseModel, Field
from typing import List, Optional
from uuid import UUID

# Response models
class HealthResponse(BaseModel):
    status: str
    message: str
    timestamp: str


class TagsResponse(BaseModel):
    tags: List[str]
    count: int


class UserProfile(BaseModel):
    id: UUID
    username: str
    bio: Optional[str]
    created_at: Optional[str]


class UserStats(BaseModel):
    courses_taken: int
    courses_rated: int
    avg_rating_given: float


class UserResponse(BaseModel):
    profile: UserProfile
    stats: UserStats


class RatingsBreakdown(BaseModel):
    lecturer: float
    material: float
    grading: float
    joy: float
    num_ratings: int


class CourseDetail(BaseModel):
    id: str
    description: str
    avg_rating: float
    tags: List[str]
    prerequisites: List[str]
    ratings_breakdown: RatingsBreakdown


class Recommendation(BaseModel):
    course_id: str
    description: str
    score: float = Field(description="Overall recommendation score (0-5)")
    collaborative_score: float = Field(description="Score from collaborative filtering")
    content_score: float = Field(description="Score from content-based filtering")
    confidence: str = Field(description="Confidence level: high, medium, or low")
    avg_rating: float = Field(description="Average rating from all users")
    tags: List[str]
    reasons: List[str] = Field(description="Human-readable reasons for recommendation")


class RecommendationsResponse(BaseModel):
    user_id: UUID
    desired_tags: Optional[List[str]]
    count: int
    recommendations: List[Recommendation]


class CourseSearchResult(BaseModel):
    id: str
    description: str
    rating: float
    tags: List[str]


class SearchResponse(BaseModel):
    query: Optional[str]
    tags_filter: Optional[List[str]]
    count: int
    courses: List[CourseSearchResult]
