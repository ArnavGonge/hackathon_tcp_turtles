import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
from typing import List, Optional, Union
from database import supabase
from uuid import UUID
import time


class DataCache:
    """Simple in-memory cache with TTL"""
    def __init__(self):
        # Dictionary to store our cached data
        self.cache = {}
        # Track when each item was cached so we know when it expires
        self.timestamps = {}

    def get(self, key: str, ttl_seconds: int = 300):
        """Get from cache if not expired"""
        if key in self.cache:
            # Check if the cached item is still fresh
            if time.time() - self.timestamps[key] < ttl_seconds:
                return self.cache[key]
            else:
                # Expired, remove
                # Item is too old, better clean it up
                del self.cache[key]
                del self.timestamps[key]
        return None

    def set(self, key: str, value):
        """Set cache value"""
        # Store the value and record the current time
        self.cache[key] = value
        self.timestamps[key] = time.time()

    def invalidate(self, key: str):
        """Invalidate specific cache entry"""
        # Remove a specific item from cache (useful when data changes)
        if key in self.cache:
            del self.cache[key]
            del self.timestamps[key]

    def clear(self):
        """Clear all cache"""
        # Wipe everything - nuclear option for when we need a fresh start
        self.cache.clear()
        self.timestamps.clear()


# Global cache instance
# Single shared cache for the entire application
_cache = DataCache()


def load_courses_data() -> pd.DataFrame:
    """Load courses - CACHED for 10 minutes"""
    # Check if we already have courses in cache
    cached = _cache.get('courses', ttl_seconds=600)
    if cached is not None:
        return cached

    # Cache miss - time to hit the database
    print("Loading courses from DB...")
    courses_response = supabase.table('courses').select(
        'id, name, source_url, description, rating'
    ).execute()

    # Convert to DataFrame and rename columns to be more descriptive
    courses_df = pd.DataFrame(courses_response.data)
    courses_df.rename(columns={'id': 'course_id', 'rating': 'avg_rating'},
                      inplace=True)

    # Store in cache for next time
    _cache.set('courses', courses_df)
    return courses_df


def load_course_tags() -> pd.DataFrame:
    """Load all course tags - CACHED for 10 minutes"""
    # Try to get tags from cache first
    cached = _cache.get('course_tags', ttl_seconds=600)
    if cached is not None:
        return cached

    # Not cached, let's fetch from database
    print("Loading course tags from DB...")
    course_tag_response = supabase.table('course_tag').select('course_id, tags(name)').execute()

    # Flatten the nested tag structure into a simple list
    course_tags_data = []
    for row in course_tag_response.data:
        if row.get('tags'):
            course_tags_data.append({
                'course_id': row['course_id'],
                'tag': row['tags']['name']
            })

    # Convert to DataFrame and cache it
    course_tags_df = pd.DataFrame(course_tags_data)
    _cache.set('course_tags', course_tags_df)
    return course_tags_df


def load_user_history(user_id: str) -> List[str]:
    """Load user's course history - OPTIMIZED"""
    # Each user gets their own cache entry
    cache_key = f'history_{user_id}'
    cached = _cache.get(cache_key, ttl_seconds=60)  # Short TTL since it changes
    if cached is not None:
        return cached

    # Load this specific user's course history
    print(f"Loading history for user {user_id}...")
    history_response = supabase.table('history').select('course_id').eq(
        'user_id', user_id
    ).execute()

    # Extract just the course IDs into a simple list
    history = [row['course_id'] for row in history_response.data]
    _cache.set(cache_key, history)
    return history


def load_user_ratings(user_id: str) -> pd.DataFrame:
    """Load only current user's ratings"""
    # User-specific cache key
    cache_key = f'ratings_{user_id}'
    cached = _cache.get(cache_key, ttl_seconds=60)
    if cached is not None:
        return cached

    # Fetch only this user's ratings - much faster than loading everyone's
    print(f"Loading ratings for user {user_id}...")
    ratings_response = supabase.table('ratings').select(
        'course_id, lecturer, material, grading, joy'
    ).eq('user_id', user_id).execute()

    ratings_df = pd.DataFrame(ratings_response.data)

    if not ratings_df.empty:
        # Add the user_id column back
        ratings_df['user_id'] = user_id
        # Calculate overall rating as average of all four categories
        ratings_df['rating'] = (
            ratings_df['lecturer'] + 
            ratings_df['material'] + 
            ratings_df['grading'] + 
            ratings_df['joy']
        ) / 4.0

    # Cache for future requests
    _cache.set(cache_key, ratings_df)
    return ratings_df


def load_all_ratings_for_collaborative() -> pd.DataFrame:
    """Load all ratings for collaborative filtering"""
    # Check cache first - this is expensive to load
    cached = _cache.get('all_ratings', ttl_seconds=300)
    if cached is not None:
        return cached

    # We need everyone's ratings to find similar users
    print("Loading all ratings for collaborative filtering...")
    ratings_response = supabase.table('ratings').select(
        'user_id, course_id, lecturer, material, grading, joy'
    ).execute()

    ratings_df = pd.DataFrame(ratings_response.data)

    if not ratings_df.empty:
        # Make sure user IDs are strings for consistency
        ratings_df['user_id'] = ratings_df['user_id'].astype(str)
        # Compute overall rating from the four sub-ratings
        ratings_df['rating'] = (
            ratings_df['lecturer'] + 
            ratings_df['material'] + 
            ratings_df['grading'] + 
            ratings_df['joy']
        ) / 4.0

    # Cache this since it's used frequently and expensive to load
    _cache.set('all_ratings', ratings_df)
    return ratings_df


# COLLABORATIVE FILTERING


def build_user_item_matrix(ratings_df: pd.DataFrame) -> pd.DataFrame:
    """Create user-item matrix"""
    # Handle edge case where we have no ratings
    if ratings_df.empty:
        return pd.DataFrame()

    # Create a matrix where rows = users, columns = courses, values = ratings
    # This is the foundation for collaborative filtering
    return ratings_df.pivot_table(
        index='user_id',
        columns='course_id',
        values='rating',
        fill_value=0  # Fill empty cells with 0 (user hasn't rated that course)
    )


def find_similar_users_cached(user_id: str, top_n: int = 15) -> pd.Series:
    """Find similar users - with caching"""
    # Check if we've already calculated similar users for this person
    cache_key = f'similar_users_{user_id}'
    cached = _cache.get(cache_key, ttl_seconds=300)
    if cached is not None:
        return cached

    # Load all ratings and build the user-item matrix
    all_ratings = load_all_ratings_for_collaborative()
    user_item_matrix = build_user_item_matrix(all_ratings)

    # Make sure the user actually exists in our data
    if user_item_matrix.empty or user_id not in user_item_matrix.index:
        return pd.Series(dtype=float)

    # Get the target user's rating vector and reshape for cosine similarity
    target_user = user_item_matrix.loc[user_id].values.reshape(1, -1)
    # Calculate how similar this user is to every other user
    similarities = cosine_similarity(target_user, user_item_matrix.values)[0]

    # Convert to Series for easier manipulation
    sim_series = pd.Series(similarities, index=user_item_matrix.index)
    # Remove the user themselves (similarity = 1.0, not useful)
    sim_series = sim_series[sim_series.index != user_id]
    # Keep only the top N most similar users
    sim_series = sim_series.sort_values(ascending=False).head(top_n)
    # Filter out very weak similarities (less than 5% similarity)
    sim_series = sim_series[sim_series > 0.05]

    # Cache the results since this is expensive to compute
    _cache.set(cache_key, sim_series)
    return sim_series


def predict_ratings_collaborative(user_id: str,
                                  candidate_courses: List[str]) -> pd.Series:
    """Predict ratings using collaborative filtering"""
    # Find users who are similar to our target user
    similar_users = find_similar_users_cached(user_id)

    # If we can't find similar users, we can't make predictions
    if similar_users.empty:
        return pd.Series(dtype=float)

    # Only load ratings for similar users and candidate courses
    print(f"Loading ratings from {len(similar_users)} similar users...")

    # Build query to get only relevant ratings
    # We already have all ratings cached, just filter them
    all_ratings = load_all_ratings_for_collaborative()

    # Filter to only ratings from similar users for courses we're considering
    similar_users_ratings = all_ratings[
        (all_ratings['user_id'].isin(similar_users.index)) &
        (all_ratings['course_id'].isin(candidate_courses))
    ]

    # If similar users haven't rated any of the candidate courses, we're stuck
    if similar_users_ratings.empty:
        return pd.Series(dtype=float)

    # Merge in the similarity scores so we can weight ratings appropriately
    similar_users_ratings = similar_users_ratings.merge(
        similar_users.rename('similarity'),
        left_on='user_id',
        right_index=True
    )

    # Predict rating for each course using weighted average of similar users' ratings
    # Higher similarity = more influence on the prediction
    predictions = similar_users_ratings.groupby('course_id').apply(
        lambda x: (x['rating'] * x['similarity']).sum() / x['similarity'].sum()
    )

    return predictions


# CONTENT-BASED FILTERING


def build_user_tag_profile(user_id: str) -> pd.Series:
    """Build user's tag preferences"""
    # Check if we've already built this user's tag profile
    cache_key = f'tag_profile_{user_id}'
    cached = _cache.get(cache_key, ttl_seconds=300)
    if cached is not None:
        return cached

    # Load the user's ratings and all course tags
    user_ratings = load_user_ratings(user_id)
    course_tags = load_course_tags()

    # Can't build a profile without data
    if user_ratings.empty or course_tags.empty:
        return pd.Series(dtype=float)

    # Use ratings >= 2.5
    # Focus on courses they liked (at least somewhat)
    high_ratings = user_ratings[user_ratings['rating'] >= 2.5]

    if high_ratings.empty:
        # Fallback to all ratings
        # If user is harsh and nothing is above 2.5, use everything
        high_ratings = user_ratings

    if high_ratings.empty:
        return pd.Series(dtype=float)

    # Join user's ratings with course tags to see which tags they liked
    user_course_tags = high_ratings.merge(course_tags, on='course_id')

    if user_course_tags.empty:
        return pd.Series(dtype=float)

    # Aggregate by tag - calculate average rating and count
    tag_profile = user_course_tags.groupby('tag').agg({
        'rating': ['mean', 'count']
    })

    tag_profile.columns = ['avg_rating', 'count']
    # Weight preference by both rating and frequency
    # If they rated many courses with a tag highly, that tag is important
    tag_profile['preference'] = tag_profile['avg_rating'] * (1 + 0.1 * tag_profile['count'])

    result = tag_profile['preference']
    # Cache the profile for future use
    _cache.set(cache_key, result)
    return result


def calculate_content_scores(candidate_courses: List[str],
                             user_tag_profile: pd.Series,
                             desired_tags: Optional[List[str]] = None) -> pd.Series:
    """Calculate content-based scores"""
    # Load course tags
    course_tags = load_course_tags()

    if course_tags.empty:
        return pd.Series(0, index=candidate_courses)

    # Filter to only tags for courses we're considering
    candidate_tags = course_tags[
        course_tags['course_id'].isin(candidate_courses)
    ]

    if candidate_tags.empty:
        return pd.Series(0, index=candidate_courses)

    # Initialize content scores
    # Start everyone at 0
    content_scores = pd.Series(0.0, index=candidate_courses)

    # If user has a tag profile, use it
    if not user_tag_profile.empty:
        # Match course tags with user's tag preferences
        candidate_tags_with_pref = candidate_tags.merge(
            user_tag_profile.rename('preference'),
            left_on='tag',
            right_index=True,
            how='inner'  # Only keep tags that match user's profile
        )

        if not candidate_tags_with_pref.empty:
            # Sum up preference scores for each course
            profile_scores = candidate_tags_with_pref.groupby('course_id')['preference'].sum()
            content_scores = content_scores.add(profile_scores, fill_value=0)

    # Add bonus for desired tags
    # If user specified career goals, boost courses with those tags
    if desired_tags:
        desired_matches = candidate_tags[
            candidate_tags['tag'].isin(desired_tags)
        ].groupby('course_id').size()

        # Give a significant bonus for alignment with career goals
        desired_bonus = desired_matches * 2.0
        content_scores = content_scores.add(desired_bonus, fill_value=0)

    # Fallback: base score for having tags
    # If we still have no scores, at least give credit for being tagged
    if content_scores.sum() == 0:
        tag_counts = candidate_tags.groupby('course_id').size()
        content_scores = tag_counts * 0.5

    # Normalize to 0-5 scale
    # Keep scores in a reasonable range
    if content_scores.sum() > 0:
        max_score = content_scores.max()
        if max_score > 5.0:
            # Scale down to fit in 0-5 range
            content_scores = (content_scores / max_score) * 5.0

    # Ensure all candidates have a score
    # Fill in 0 for any courses we somehow missed
    content_scores = content_scores.reindex(candidate_courses, fill_value=0)

    return content_scores


# RECOMMENDATION GENERATION


def generate_reasons(row: pd.Series, 
                    user_tag_profile: pd.Series,
                    desired_tags: Optional[List[str]]) -> List[str]:
    """Generate recommendation reasons"""
    # Build a list of human-readable reasons for why we're recommending this
    reasons = []

    # Check collaborative filtering score
    if row['collab_score'] >= 4.5:
        reasons.append(f"Students like you rated this {row['collab_score']:.1f} stars")
    elif row['collab_score'] >= 4.0:
        reasons.append(f"Highly rated by similar students ({row['collab_score']:.1f} stars)")

    # Check if course matches user's interests
    if not user_tag_profile.empty and row['tags']:
        # Find which tags match the user's profile
        matching = [t for t in row['tags'] if t in user_tag_profile.index]
        if matching:
            # Show the top 3 most relevant tags
            top_matches = sorted(matching, key=lambda t: user_tag_profile[t], reverse=True)[:3]
            reasons.append(f"Matches interests: {', '.join(top_matches)}")

    # Check if course aligns with career goals
    if desired_tags and row['tags']:
        matching_desired = set(row['tags']) & set(desired_tags)
        if matching_desired:
            reasons.append(f"Prepares for: {', '.join(matching_desired)}")

    # Check overall popularity
    if row['avg_rating'] >= 4.5:
        reasons.append(f"Popular course ({row['avg_rating']:.1f} stars)")

    # Fallback reason if we haven't found any specific reasons yet
    if row['content_score'] > 0 and not reasons:
        reasons.append("Relevant to your interests")

    # Always return at least one reason
    return reasons if reasons else ["Recommended based on course popularity"]


def get_recommendations(user_id: Union[UUID, str],
                       desired_tags: Optional[List[str]] = None,
                       top_n: int = 10,
                       collab_weight: float = 0.6,
                       content_weight: float = 0.4) -> pd.DataFrame:
    """Get course recommendations"""

    # Convert UUID to string if needed
    # Handle both UUID objects and strings
    if isinstance(user_id, UUID):
        user_id = str(user_id)

    # Start the recommendation process
    print(f"\n=== Getting recommendations for user {user_id} ===")
    start_time = time.time()

    # Load data using cache
    # These functions will use cached data if available
    courses_df = load_courses_data()
    taken_courses = load_user_history(user_id)

    print(f"User has taken {len(taken_courses)} courses")

    # Get candidate courses
    # Don't recommend courses they've already taken
    candidates = courses_df[~courses_df['course_id'].isin(taken_courses)].copy()

    # Filter by desired tags if specified
    # If user wants to prepare for a specific career, focus on relevant courses
    if desired_tags:
        course_tags = load_course_tags()
        if not course_tags.empty:
            # Find courses that have at least one of the desired tags
            courses_with_tags = course_tags[
                course_tags['tag'].isin(desired_tags)
            ]['course_id'].unique()

            candidates = candidates[candidates['course_id'].isin(courses_with_tags)]
            print(f"Filtered to {len(candidates)} courses with desired tags")

    # If we have no candidates, we're done
    if candidates.empty:
        print("No candidate courses found")
        return pd.DataFrame()

    candidate_courses = candidates['course_id'].tolist()

    # Collaborative filtering
    # Predict ratings based on what similar users liked
    collab_predictions = predict_ratings_collaborative(user_id, candidate_courses)
    print(f"Collaborative predictions: {len(collab_predictions)} courses")

    # Content-based filtering
    # Score courses based on how well they match user's interests
    user_tag_profile = build_user_tag_profile(user_id)
    print(f"User tag profile: {len(user_tag_profile)} tags")

    content_scores = calculate_content_scores(
        candidate_courses, user_tag_profile, desired_tags
    )

    # Merge scores
    # Combine both collaborative and content-based scores
    candidates = candidates.set_index('course_id')
    candidates['collab_score'] = collab_predictions
    candidates['content_score'] = content_scores
    candidates = candidates.fillna(0)

    print(f"Collab - Non-zero: {(candidates['collab_score'] > 0).sum()}, Mean: {candidates['collab_score'].mean():.2f}")
    print(f"Content - Non-zero: {(candidates['content_score'] > 0).sum()}, Mean: {candidates['content_score'].mean():.2f}")

    # Calculate final score
    # Determine which courses have collaborative scores
    has_collab = candidates['collab_score'] > 0

    # For courses with collaborative scores, use weighted average
    candidates.loc[has_collab, 'final_score'] = (
        collab_weight * candidates.loc[has_collab, 'collab_score'] +
        content_weight * candidates.loc[has_collab, 'content_score']
    )

    # For courses without collaborative scores, rely more on content and popularity
    candidates.loc[~has_collab, 'final_score'] = (
        0.6 * candidates.loc[~has_collab, 'content_score'] +
        0.4 * candidates.loc[~has_collab, 'avg_rating']
    )

    # Set confidence level based on whether we have collaborative data
    # High confidence when we have similar users' opinions
    candidates['confidence'] = has_collab.map({True: 'high', False: 'medium'})

    # Add tags
    # Attach tag information to each course for display
    course_tags = load_course_tags()
    if not course_tags.empty:
        # Group tags by course
        course_tags_grouped = course_tags.groupby('course_id')['tag'].apply(list)
        candidates['tags'] = course_tags_grouped
    else:
        # No tags available, use empty lists
        candidates['tags'] = [[] for _ in range(len(candidates))]

    # Make sure tags is always a list
    candidates['tags'] = candidates['tags'].apply(lambda x: x if isinstance(x, list) else [])

    # Generate reasons
    # Create human-readable explanations for each recommendation
    candidates['reasons'] = candidates.apply(
        lambda row: generate_reasons(row, user_tag_profile, desired_tags), 
        axis=1
    )

    # Sort and return
    # Return the top N courses sorted by final score
    results = candidates.sort_values('final_score', ascending=False).head(top_n)

    # Log how long this took
    elapsed = time.time() - start_time
    print(f"Returning {len(results)} recommendations in {elapsed:.2f}s")

    return results.reset_index()


# CACHE MANAGEMENT


def invalidate_user_cache(user_id: str):
    """Invalidate cache for a specific user (call when user adds ratings)"""
    # When a user adds new ratings or courses, their cached data is stale
    # Clear all their user-specific cache entries
    _cache.invalidate(f'ratings_{user_id}')
    _cache.invalidate(f'history_{user_id}')
    _cache.invalidate(f'tag_profile_{user_id}')
    _cache.invalidate(f'similar_users_{user_id}')
    # Also invalidate all_ratings since it affects collaborative filtering
    # All users' collaborative predictions need to be recalculated
    _cache.invalidate('all_ratings')


def clear_all_cache():
    """Clear entire cache"""
    # Nuclear option - wipe everything and start fresh
    # Useful for maintenance or when data has been bulk updated
    _cache.clear()
