# helpers.py
from typing import Optional, Dict
from database import supabase, get_single_record, count_records
from uuid import UUID

def get_user_profile(user_id: UUID) -> Optional[Dict]:
    """Get user profile"""
    # Convert UUID to string for Supabase query
    user = get_single_record('users', {'id': str(user_id)}, 'id, username, bio, created_at')
    
    if user and user.get('created_at'):
        # Format timestamp
        user['created_at'] = user['created_at'].split('T')[0] if 'T' in user['created_at'] else user['created_at']
    
    return user

def get_user_stats(user_id: UUID) -> Dict:
    """Get user statistics"""
    # Convert UUID to string for Supabase query
    user_id_str = str(user_id)
    
    courses_taken = count_records('history', {'user_id': user_id_str})
    courses_rated = count_records('ratings', {'user_id': user_id_str})
    
    # Get average rating
    ratings = supabase.table('ratings').select('lecturer, material, grading, joy').eq('user_id', user_id_str).execute()
    
    if ratings.data:
        total = sum((r['lecturer'] + r['material'] + r['grading'] + r['joy']) / 4.0 for r in ratings.data)
        avg_rating = total / len(ratings.data)
    else:
        avg_rating = 0
    
    return {
        'courses_taken': courses_taken,
        'courses_rated': courses_rated,
        'avg_rating_given': round(avg_rating, 2)
    }

def get_course_details(course_id: str) -> Optional[Dict]:
    """Get course details"""
    course = get_single_record('courses', {'id': course_id})
    if not course:
        return None
    
    # Get tags (with join)
    tags_response = supabase.table('course_tag').select('tags(name)').eq('course_id', course_id).execute()
    tags = [row['tags']['name'] for row in tags_response.data if row.get('tags')]
    
    # Get prerequisites
    prereqs_response = supabase.table('prereqs').select('prereq_id').eq('course_id', course_id).execute()
    prerequisites = [row['prereq_id'] for row in prereqs_response.data]
    
    # Get ratings breakdown
    ratings_response = supabase.table('ratings').select('lecturer, material, grading, joy').eq('course_id', course_id).execute()
    
    if ratings_response.data:
        ratings = ratings_response.data
        breakdown = {
            'lecturer': round(sum(r['lecturer'] for r in ratings) / len(ratings), 2),
            'material': round(sum(r['material'] for r in ratings) / len(ratings), 2),
            'grading': round(sum(r['grading'] for r in ratings) / len(ratings), 2),
            'joy': round(sum(r['joy'] for r in ratings) / len(ratings), 2),
            'num_ratings': len(ratings)
        }
    else:
        breakdown = {'lecturer': 0, 'material': 0, 'grading': 0, 'joy': 0, 'num_ratings': 0}
    
    return {
        'id': course['id'],
        'description': course['description'],
        'avg_rating': round(float(course['rating']), 2) if course['rating'] else 0,
        'tags': tags,
        'prerequisites': prerequisites,
        'ratings_breakdown': breakdown
    }