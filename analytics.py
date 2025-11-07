"""
Analytics tracking module for XThreadMaster
Tracks user content generation activity and provides insights
Now using Supabase for persistent storage
"""

import hashlib
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional
import streamlit as st
from supabase import create_client, Client

# Initialize Supabase client (lazy-loaded)
_supabase_client: Optional[Client] = None

def get_supabase() -> Client:
    """Get or create Supabase client"""
    global _supabase_client
    if _supabase_client is None:
        url = st.secrets.get("SUPABASE_URL")
        key = st.secrets.get("SUPABASE_KEY")
        if not url or not key:
            raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in Streamlit secrets")
        _supabase_client = create_client(url, key)
    return _supabase_client

def get_user_hash(email: str) -> str:
    """
    Create a hashed user ID from email for privacy
    Uses SHA256 to anonymize email addresses
    """
    return hashlib.sha256(email.encode()).hexdigest()[:16]

def load_user_analytics(email: str) -> Dict:
    """
    Load analytics data for a user from Supabase
    Returns empty structure if no data exists
    """
    if not email or not email.strip():
        return get_empty_analytics()

    try:
        supabase = get_supabase()
        user_hash = get_user_hash(email)

        # Fetch analytics record
        response = supabase.table("analytics").select("*").eq("user_hash", user_hash).execute()

        if response.data and len(response.data) > 0:
            record = response.data[0]
            return {
                "user_created": record["user_created"],
                "last_updated": record["last_updated"],
                "total_generations": record["total_generations"],
                "generations_by_platform": record["generations_by_platform"],
                "generations_by_tone": record["generations_by_tone"],
                "templates_used": record["templates_used"],
                "daily_activity": record["daily_activity"]
            }
        else:
            return get_empty_analytics()
    except Exception as e:
        print(f"Error loading analytics: {e}")
        return get_empty_analytics()

def get_empty_analytics() -> Dict:
    """Return empty analytics structure"""
    return {
        "user_created": datetime.now().isoformat(),
        "last_updated": datetime.now().isoformat(),
        "total_generations": 0,
        "generations_by_platform": {
            "X Thread": 0,
            "LinkedIn Post": 0,
            "Instagram Carousel": 0
        },
        "generations_by_tone": {},
        "templates_used": {},
        "daily_activity": {}
    }

def save_user_analytics(email: str, data: Dict):
    """Save analytics data for a user to Supabase"""
    if not email or not email.strip():
        return

    try:
        supabase = get_supabase()
        user_hash = get_user_hash(email)
        data["last_updated"] = datetime.now().isoformat()

        # Upsert (insert or update) the analytics record
        supabase.table("analytics").upsert({
            "user_hash": user_hash,
            "user_email": email,  # Store for reference (hashed for privacy)
            "user_created": data.get("user_created", datetime.now().isoformat()),
            "last_updated": data["last_updated"],
            "total_generations": data["total_generations"],
            "generations_by_platform": data["generations_by_platform"],
            "generations_by_tone": data["generations_by_tone"],
            "templates_used": data["templates_used"],
            "daily_activity": data["daily_activity"]
        }, on_conflict="user_hash").execute()
    except Exception as e:
        print(f"Error saving analytics: {e}")

def track_generation(
    email: str,
    platform: str,
    tone: str,
    length: Optional[int],
    topic: str,
    template_used: Optional[str] = None,
    template_id: Optional[str] = None
):
    """
    Track a content generation event

    Args:
        email: User's email
        platform: Platform (X Thread, LinkedIn Post, Instagram Carousel)
        tone: Content tone (Casual, Funny, Pro, Degen)
        length: Content length (number of tweets/slides, None for LinkedIn)
        topic: Content topic/subject
        template_used: Name of template if used
        template_id: ID of template if used
    """
    if not email or not email.strip():
        return

    try:
        supabase = get_supabase()
        user_hash = get_user_hash(email)

        # Load current analytics
        analytics = load_user_analytics(email)

        # Update counters
        analytics["total_generations"] += 1

        # Platform breakdown
        if platform in analytics["generations_by_platform"]:
            analytics["generations_by_platform"][platform] += 1
        else:
            analytics["generations_by_platform"][platform] = 1

        # Tone breakdown
        if tone in analytics["generations_by_tone"]:
            analytics["generations_by_tone"][tone] += 1
        else:
            analytics["generations_by_tone"][tone] = 1

        # Template tracking
        if template_used and template_id:
            if template_id in analytics["templates_used"]:
                analytics["templates_used"][template_id]["count"] += 1
            else:
                analytics["templates_used"][template_id] = {
                    "name": template_used,
                    "count": 1,
                    "platform": platform
                }

        # Daily activity
        today = date.today().isoformat()
        if today in analytics["daily_activity"]:
            analytics["daily_activity"][today] += 1
        else:
            analytics["daily_activity"][today] = 1

        # Save analytics
        save_user_analytics(email, analytics)

        # Add to generation history (separate table)
        supabase.table("generation_history").insert({
            "user_hash": user_hash,
            "platform": platform,
            "tone": tone,
            "length": length,
            "topic": topic[:100] if topic else "",
            "template_used": template_used,
            "template_id": template_id,
            "timestamp": datetime.now().isoformat()
        }).execute()

        # Clean old history (keep last 50)
        supabase.rpc("clean_old_generation_history").execute()
    except Exception as e:
        print(f"Error tracking generation: {e}")

def get_analytics_summary(email: str) -> Optional[Dict]:
    """
    Get a summary of user analytics for dashboard display

    Returns:
        Dict with formatted analytics ready for display
    """
    if not email or not email.strip():
        return None

    try:
        supabase = get_supabase()
        user_hash = get_user_hash(email)

        # Load analytics
        analytics = load_user_analytics(email)
        total_gens = analytics["total_generations"]

        if total_gens == 0:
            return None

        # Get most used platform
        platform_counts = analytics["generations_by_platform"]
        most_used_platform = max(platform_counts.items(), key=lambda x: x[1])[0] if platform_counts else "N/A"

        # Get most used tone
        tone_counts = analytics["generations_by_tone"]
        most_used_tone = max(tone_counts.items(), key=lambda x: x[1])[0] if tone_counts else "N/A"

        # Get most used template
        templates = analytics["templates_used"]
        most_used_template = None
        if templates:
            top_template_id = max(templates.items(), key=lambda x: x[1]["count"])[0]
            most_used_template = {
                "name": templates[top_template_id]["name"],
                "count": templates[top_template_id]["count"]
            }

        # Recent activity (last 7 days)
        daily_activity = analytics["daily_activity"]
        recent_days = sorted(daily_activity.keys(), reverse=True)[:7]
        recent_activity = {day: daily_activity[day] for day in recent_days}

        # Calculate average per day (lifetime)
        if daily_activity:
            avg_per_day = total_gens / len(daily_activity)
        else:
            avg_per_day = 0

        # Get recent history from database (last 10)
        recent_history = []
        try:
            response = supabase.table("generation_history")\
                .select("*")\
                .eq("user_hash", user_hash)\
                .order("timestamp", desc=True)\
                .limit(10)\
                .execute()

            if response.data:
                recent_history = response.data
        except Exception:
            pass

        return {
            "total_generations": total_gens,
            "platform_breakdown": platform_counts,
            "tone_breakdown": tone_counts,
            "most_used_platform": most_used_platform,
            "most_used_tone": most_used_tone,
            "most_used_template": most_used_template,
            "templates_used": templates,
            "recent_activity": recent_activity,
            "avg_per_day": round(avg_per_day, 1),
            "recent_history": recent_history,
            "user_since": analytics.get("user_created", "Unknown")
        }
    except Exception as e:
        print(f"Error getting analytics summary: {e}")
        return None

def get_daily_activity_chart_data(email: str, days: int = 30) -> List[Dict]:
    """
    Get daily activity data formatted for charts

    Returns:
        List of dicts with 'date' and 'count' keys for the last N days
    """
    if not email or not email.strip():
        return []

    try:
        analytics = load_user_analytics(email)
        daily_activity = analytics["daily_activity"]

        # Get last N days
        today = date.today()
        date_range = [(today - timedelta(days=i)).isoformat() for i in range(days-1, -1, -1)]

        chart_data = []
        for d in date_range:
            chart_data.append({
                "date": d,
                "count": daily_activity.get(d, 0)
            })

        return chart_data
    except Exception as e:
        print(f"Error getting chart data: {e}")
        return []

def track_posted_tweet(email: str, tweet_id: str, topic: str, tone: str, template_used: Optional[str] = None):
    """
    Track a tweet that was successfully posted to X

    Args:
        email: User's email
        tweet_id: The ID of the posted tweet (from X API)
        topic: Tweet topic/subject
        tone: Content tone
        template_used: Template name if used
    """
    if not email or not email.strip() or not tweet_id:
        return

    try:
        supabase = get_supabase()
        user_hash = get_user_hash(email)

        # Insert posted tweet record
        supabase.table("posted_tweets").insert({
            "user_hash": user_hash,
            "tweet_id": tweet_id,
            "posted_at": datetime.now().isoformat(),
            "topic": topic[:100] if topic else "",
            "tone": tone,
            "template_used": template_used,
            "likes": 0,
            "retweets": 0,
            "replies": 0,
            "views": 0,
            "bookmarks": 0,
            "last_fetched": None
        }).execute()
    except Exception as e:
        print(f"Error tracking posted tweet: {e}")

def fetch_tweet_metrics(email: str, tweet_id: str, client) -> Optional[Dict]:
    """
    Fetch engagement metrics for a specific tweet using X API v2

    Args:
        email: User's email
        tweet_id: The tweet ID to fetch metrics for
        client: Authenticated tweepy.Client instance

    Returns:
        Dict with updated metrics or None if failed
    """
    try:
        # Fetch tweet with public metrics
        tweet = client.get_tweet(
            id=tweet_id,
            tweet_fields=["public_metrics", "created_at"]
        )

        if tweet.data:
            metrics = tweet.data.public_metrics
            return {
                "likes": metrics.get("like_count", 0),
                "retweets": metrics.get("retweet_count", 0),
                "replies": metrics.get("reply_count", 0),
                "views": metrics.get("impression_count", 0),
                "bookmarks": metrics.get("bookmark_count", 0)
            }
        return None
    except Exception as e:
        print(f"Error fetching tweet metrics: {e}")
        return None

def refresh_all_tweet_metrics(email: str, client) -> int:
    """
    Refresh engagement metrics for all posted tweets

    Args:
        email: User's email
        client: Authenticated tweepy.Client instance

    Returns:
        Number of tweets successfully refreshed
    """
    if not email or not email.strip():
        return 0

    try:
        supabase = get_supabase()
        user_hash = get_user_hash(email)

        # Get all posted tweets for user
        response = supabase.table("posted_tweets")\
            .select("*")\
            .eq("user_hash", user_hash)\
            .execute()

        if not response.data:
            return 0

        refreshed_count = 0

        for tweet_record in response.data:
            tweet_id = tweet_record["tweet_id"]
            metrics = fetch_tweet_metrics(email, tweet_id, client)

            if metrics:
                # Update metrics in database
                supabase.table("posted_tweets")\
                    .update({
                        "likes": metrics["likes"],
                        "retweets": metrics["retweets"],
                        "replies": metrics["replies"],
                        "views": metrics["views"],
                        "bookmarks": metrics["bookmarks"],
                        "last_fetched": datetime.now().isoformat()
                    })\
                    .eq("tweet_id", tweet_id)\
                    .execute()

                refreshed_count += 1

        return refreshed_count
    except Exception as e:
        print(f"Error refreshing tweet metrics: {e}")
        return 0

def get_engagement_summary(email: str) -> Optional[Dict]:
    """
    Get engagement metrics summary for analytics dashboard

    Returns:
        Dict with engagement stats or None if no data
    """
    if not email or not email.strip():
        return None

    try:
        supabase = get_supabase()
        user_hash = get_user_hash(email)

        # Get all posted tweets for user
        response = supabase.table("posted_tweets")\
            .select("*")\
            .eq("user_hash", user_hash)\
            .execute()

        if not response.data or len(response.data) == 0:
            return None

        posted_tweets = response.data

        # Calculate totals
        total_likes = sum(t["likes"] for t in posted_tweets)
        total_retweets = sum(t["retweets"] for t in posted_tweets)
        total_replies = sum(t["replies"] for t in posted_tweets)
        total_views = sum(t["views"] for t in posted_tweets)
        total_bookmarks = sum(t["bookmarks"] for t in posted_tweets)

        total_posts = len(posted_tweets)
        total_engagement = total_likes + total_retweets + total_replies + total_bookmarks

        # Find best performing tweet
        best_tweet = None
        best_engagement = 0

        for tweet_record in posted_tweets:
            engagement = (
                tweet_record["likes"] +
                tweet_record["retweets"] +
                tweet_record["replies"] +
                tweet_record["bookmarks"]
            )
            if engagement > best_engagement:
                best_engagement = engagement
                best_tweet = {
                    "tweet_id": tweet_record["tweet_id"],
                    "topic": tweet_record["topic"],
                    "engagement": engagement,
                    "metrics": {
                        "likes": tweet_record["likes"],
                        "retweets": tweet_record["retweets"],
                        "replies": tweet_record["replies"],
                        "views": tweet_record["views"],
                        "bookmarks": tweet_record["bookmarks"]
                    }
                }

        # Calculate averages
        avg_likes = total_likes / total_posts if total_posts > 0 else 0
        avg_retweets = total_retweets / total_posts if total_posts > 0 else 0
        avg_engagement = total_engagement / total_posts if total_posts > 0 else 0

        return {
            "total_posts": total_posts,
            "total_likes": total_likes,
            "total_retweets": total_retweets,
            "total_replies": total_replies,
            "total_views": total_views,
            "total_bookmarks": total_bookmarks,
            "total_engagement": total_engagement,
            "avg_likes": round(avg_likes, 1),
            "avg_retweets": round(avg_retweets, 1),
            "avg_engagement": round(avg_engagement, 1),
            "best_tweet": best_tweet
        }
    except Exception as e:
        print(f"Error getting engagement summary: {e}")
        return None

def save_thread_to_history(email: str, platform: str, content: str):
    """
    Save a generated thread to history (Pro users only)
    Keeps last 10 threads per user

    Args:
        email: User's email
        platform: Platform (X Thread, LinkedIn Post, Instagram Carousel)
        content: The generated content
    """
    if not email or not email.strip() or not content:
        return

    try:
        supabase = get_supabase()
        user_hash = get_user_hash(email)

        # Insert thread to history
        supabase.table("thread_history").insert({
            "user_hash": user_hash,
            "platform": platform,
            "content": content,
            "timestamp": datetime.now().isoformat()
        }).execute()

        # Clean old history (keep last 10)
        supabase.rpc("clean_old_thread_history").execute()
    except Exception as e:
        print(f"Error saving thread to history: {e}")

def get_thread_history(email: str, limit: int = 10) -> List[Dict]:
    """
    Get thread history for a user

    Args:
        email: User's email
        limit: Number of threads to return (default 10)

    Returns:
        List of thread history entries
    """
    if not email or not email.strip():
        return []

    try:
        supabase = get_supabase()
        user_hash = get_user_hash(email)

        response = supabase.table("thread_history")\
            .select("*")\
            .eq("user_hash", user_hash)\
            .order("timestamp", desc=True)\
            .limit(limit)\
            .execute()

        return response.data if response.data else []
    except Exception as e:
        print(f"Error getting thread history: {e}")
        return []

def clear_user_analytics(email: str) -> bool:
    """
    Clear all analytics data for a user
    Useful for privacy-conscious users who want to reset their data

    Returns:
        True if data was cleared successfully, False otherwise
    """
    if not email or not email.strip():
        return False

    try:
        supabase = get_supabase()
        user_hash = get_user_hash(email)

        # Delete all user data
        supabase.table("analytics").delete().eq("user_hash", user_hash).execute()
        supabase.table("generation_history").delete().eq("user_hash", user_hash).execute()
        supabase.table("posted_tweets").delete().eq("user_hash", user_hash).execute()
        supabase.table("thread_history").delete().eq("user_hash", user_hash).execute()

        return True
    except Exception as e:
        print(f"Error clearing analytics: {e}")
        return False
