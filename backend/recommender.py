# recommender.py
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
from typing import List, Optional, Union
from database import supabase
from uuid import UUID

def load_all_data():
    """Load all data via REST API"""
    
    # Ratings
    print("Loading ratings...")
    ratings_response = supabase.table('ratings').select('user_id, course_id, lecturer, material, grading, joy').execute()
    ratings_df = pd.DataFrame(ratings_response.data)
    
    if not ratings_df.empty:
        # Convert user_id to string for consistent comparison
        ratings_df['user_id'] = ratings_df['user_id'].astype(str)
        
        ratings_df['rating'] = (
            ratings_df['lecturer'] + 
            ratings_df['material'] + 
            ratings_df['grading'] + 
            ratings_df['joy']
        ) / 4.0
    
    # Courses
    print("Loading courses...")
    courses_response = supabase.table('courses').select('id, description, rating').execute()
    courses_df = pd.DataFrame(courses_response.data)
    courses_df.rename(columns={'id': 'course_id', 'rating': 'avg_rating'}, inplace=True)
    
    # Course tags
    print("Loading course tags...")
    course_tag_response = supabase.table('course_tag').select('course_id, tags(name)').execute()
    
    course_tags_data = []
    for row in course_tag_response.data:
        if row.get('tags'):
            course_tags_data.append({
                'course_id': row['course_id'],
                'tag': row['tags']['name']
            })
    course_tags_df = pd.DataFrame(course_tags_data)
    
    # History
    print("Loading history...")
    history_response = supabase.table('history').select('user_id, course_id').execute()
    history_df = pd.DataFrame(history_response.data)
    
    if not history_df.empty:
        # Convert user_id to string for consistent comparison
        history_df['user_id'] = history_df['user_id'].astype(str)
    
    print(f"Loaded: {len(ratings_df)} ratings, {len(courses_df)} courses, {len(course_tags_df)} tags, {len(history_df)} history")
    
    return ratings_df, courses_df, course_tags_df, history_df

def build_user_item_matrix(ratings_df: pd.DataFrame) -> pd.DataFrame:
    """Create user-item matrix"""
    if ratings_df.empty:
        return pd.DataFrame()
    
    return ratings_df.pivot_table(
        index='user_id',
        columns='course_id',
        values='rating',
        fill_value=0
    )

def find_similar_users_vectorized(user_id: str, user_item_matrix: pd.DataFrame, 
                                   top_n: int = 15) -> pd.Series:
    """Find similar users"""
    if user_item_matrix.empty or user_id not in user_item_matrix.index:
        return pd.Series(dtype=float)
    
    target_user = user_item_matrix.loc[user_id].values.reshape(1, -1)
    similarities = cosine_similarity(target_user, user_item_matrix.values)[0]
    
    sim_series = pd.Series(similarities, index=user_item_matrix.index)
    sim_series = sim_series[sim_series.index != user_id]
    sim_series = sim_series.sort_values(ascending=False).head(top_n)
    sim_series = sim_series[sim_series > 0.05]
    
    return sim_series

def predict_ratings_collaborative(user_id: str, 
                                  candidate_courses: List[str],
                                  ratings_df: pd.DataFrame,
                                  user_item_matrix: pd.DataFrame) -> pd.Series:
    """Predict ratings using collaborative filtering"""
    similar_users = find_similar_users_vectorized(user_id, user_item_matrix)
    
    if similar_users.empty or ratings_df.empty:
        return pd.Series(dtype=float)
    
    similar_users_ratings = ratings_df[
        (ratings_df['user_id'].isin(similar_users.index)) &
        (ratings_df['course_id'].isin(candidate_courses))
    ]
    
    if similar_users_ratings.empty:
        return pd.Series(dtype=float)
    
    similar_users_ratings = similar_users_ratings.merge(
        similar_users.rename('similarity'),
        left_on='user_id',
        right_index=True
    )
    
    predictions = similar_users_ratings.groupby('course_id').apply(
        lambda x: (x['rating'] * x['similarity']).sum() / x['similarity'].sum()
    )
    
    return predictions

def build_user_tag_profile_vectorized(user_id: str, 
                                      ratings_df: pd.DataFrame,
                                      course_tags_df: pd.DataFrame) -> pd.Series:
    """Build user's tag preferences"""
    if ratings_df.empty or course_tags_df.empty:
        return pd.Series(dtype=float)
    
    user_high_ratings = ratings_df[
        (ratings_df['user_id'] == user_id) & 
        (ratings_df['rating'] >= 4.0)
    ]
    
    if user_high_ratings.empty:
        return pd.Series(dtype=float)
    
    user_course_tags = user_high_ratings.merge(course_tags_df, on='course_id')
    
    if user_course_tags.empty:
        return pd.Series(dtype=float)
    
    tag_profile = user_course_tags.groupby('tag').agg({
        'rating': ['mean', 'count']
    })
    
    tag_profile.columns = ['avg_rating', 'count']
    tag_profile['preference'] = tag_profile['avg_rating'] * (1 + 0.1 * tag_profile['count'])
    
    return tag_profile['preference']

def calculate_content_scores(candidate_courses: List[str],
                             user_tag_profile: pd.Series,
                             course_tags_df: pd.DataFrame,
                             desired_tags: Optional[List[str]] = None) -> pd.Series:
    """Calculate content-based scores"""
    if course_tags_df.empty:
        return pd.Series(0, index=candidate_courses)
    
    candidate_tags = course_tags_df[
        course_tags_df['course_id'].isin(candidate_courses)
    ]
    
    if candidate_tags.empty or user_tag_profile.empty:
        return pd.Series(0, index=candidate_courses)
    
    candidate_tags = candidate_tags.merge(
        user_tag_profile.rename('preference'),
        left_on='tag',
        right_index=True,
        how='left'
    ).fillna(0)
    
    content_scores = candidate_tags.groupby('course_id')['preference'].sum()
    
    if desired_tags:
        desired_bonus = candidate_tags[
            candidate_tags['tag'].isin(desired_tags)
        ].groupby('course_id').size() * 2.0
        
        content_scores = content_scores.add(desired_bonus, fill_value=0)
    
    content_scores = content_scores / 2.0
    content_scores = content_scores.clip(upper=5.0)
    
    return content_scores

def generate_reasons(row: pd.Series, 
                    user_tag_profile: pd.Series,
                    desired_tags: Optional[List[str]]) -> List[str]:
    """Generate recommendation reasons"""
    reasons = []
    
    if row['collab_score'] >= 4.5:
        reasons.append(f"Students like you rated this {row['collab_score']:.1f} stars")
    elif row['collab_score'] >= 4.0:
        reasons.append(f"Highly rated by similar students ({row['collab_score']:.1f} stars)")
    
    if not user_tag_profile.empty and row['tags']:
        matching = [t for t in row['tags'] if t in user_tag_profile.index]
        if matching:
            top_matches = sorted(matching, key=lambda t: user_tag_profile[t], reverse=True)[:3]
            reasons.append(f"Matches interests: {', '.join(top_matches)}")
    
    if desired_tags and row['tags']:
        matching_desired = set(row['tags']) & set(desired_tags)
        if matching_desired:
            reasons.append(f"Prepares for: {', '.join(matching_desired)}")
    
    if row['avg_rating'] >= 4.5:
        reasons.append(f"Popular course ({row['avg_rating']:.1f} stars)")
    
    return reasons

def get_recommendations(user_id: Union[UUID, str],  # Accept both UUID and string
                       desired_tags: Optional[List[str]] = None,
                       top_n: int = 10,
                       collab_weight: float = 0.6,
                       content_weight: float = 0.4) -> pd.DataFrame:
    """Get course recommendations"""
    
    # Convert UUID to string if needed
    if isinstance(user_id, UUID):
        user_id = str(user_id)
    
    ratings_df, courses_df, course_tags_df, history_df = load_all_data()
    
    if courses_df.empty:
        return pd.DataFrame()
    
    # Get courses not taken
    taken_courses = history_df[history_df['user_id'] == user_id]['course_id'].tolist() if not history_df.empty else []
    candidates = courses_df[~courses_df['course_id'].isin(taken_courses)].copy()
    
    # Filter by desired tags
    if desired_tags and not course_tags_df.empty:
        courses_with_tags = course_tags_df[
            course_tags_df['tag'].isin(desired_tags)
        ]['course_id'].unique()
        
        candidates = candidates[candidates['course_id'].isin(courses_with_tags)]
    
    if candidates.empty:
        return pd.DataFrame()
    
    candidate_courses = candidates['course_id'].tolist()
    
    # Build user-item matrix
    user_item_matrix = build_user_item_matrix(ratings_df)
    
    # Collaborative filtering
    collab_predictions = predict_ratings_collaborative(
        user_id, candidate_courses, ratings_df, user_item_matrix
    )
    
    # Content-based filtering
    user_tag_profile = build_user_tag_profile_vectorized(
        user_id, ratings_df, course_tags_df
    )
    
    content_scores = calculate_content_scores(
        candidate_courses, user_tag_profile, course_tags_df, desired_tags
    )
    
    # Merge scores
    candidates = candidates.set_index('course_id')
    candidates['collab_score'] = collab_predictions
    candidates['content_score'] = content_scores
    candidates = candidates.fillna(0)
    
    # Calculate final score
    has_collab = candidates['collab_score'] > 0
    
    candidates.loc[has_collab, 'final_score'] = (
        collab_weight * candidates.loc[has_collab, 'collab_score'] +
        content_weight * candidates.loc[has_collab, 'content_score']
    )
    
    candidates.loc[~has_collab, 'final_score'] = (
        0.6 * candidates.loc[~has_collab, 'content_score'] +
        0.4 * candidates.loc[~has_collab, 'avg_rating']
    )
    
    candidates['confidence'] = has_collab.map({True: 'high', False: 'medium'})
    
    # Add tags
    if not course_tags_df.empty:
        course_tags_grouped = course_tags_df.groupby('course_id')['tag'].apply(list)
        candidates['tags'] = course_tags_grouped
    else:
        candidates['tags'] = [[] for _ in range(len(candidates))]
    
    candidates['tags'] = candidates['tags'].apply(lambda x: x if isinstance(x, list) else [])
    
    # Generate reasons
    candidates['reasons'] = candidates.apply(
        lambda row: generate_reasons(row, user_tag_profile, desired_tags), 
        axis=1
    )
    
    # Sort and return
    results = candidates.sort_values('final_score', ascending=False).head(top_n)
    
    return results.reset_index()