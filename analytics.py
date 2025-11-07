"""
Analytics tracking module for XThreadMaster
Tracks user content generation activity and provides insights
"""

import json
import os
from datetime import datetime, date
from typing import Dict, List, Optional
import hashlib

# Analytics data directory
ANALYTICS_DIR = "analytics_data"

def ensure_analytics_dir():
    """Ensure analytics data directory exists"""
    if not os.path.exists(ANALYTICS_DIR):
        os.makedirs(ANALYTICS_DIR)

def get_user_hash(email: str) -> str:
    """
    Create a hashed user ID from email for privacy
    Uses SHA256 to anonymize email addresses
    """
    return hashlib.sha256(email.encode()).hexdigest()[:16]

def get_analytics_file(email: str) -> str:
    """Get the analytics file path for a user"""
    ensure_analytics_dir()
    user_hash = get_user_hash(email)
    return os.path.join(ANALYTICS_DIR, f"user_{user_hash}.json")

def load_user_analytics(email: str) -> Dict:
    """
    Load analytics data for a user
    Returns empty structure if no data exists
    """
    if not email or not email.strip():
        return get_empty_analytics()

    filepath = get_analytics_file(email)

    if not os.path.exists(filepath):
        return get_empty_analytics()

    try:
        with open(filepath, 'r') as f:
            data = json.load(f)
        return data
    except Exception:
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
        "daily_activity": {},
        "generation_history": [],
        "posted_tweets": {}  # Store tweet IDs with their metrics
    }

def save_user_analytics(email: str, data: Dict):
    """Save analytics data for a user"""
    if not email or not email.strip():
        return

    ensure_analytics_dir()
    filepath = get_analytics_file(email)
    data["last_updated"] = datetime.now().isoformat()

    try:
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
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

    # Add to generation history (keep last 50)
    history_entry = {
        "timestamp": datetime.now().isoformat(),
        "platform": platform,
        "tone": tone,
        "length": length,
        "topic": topic[:100] if topic else "",  # Truncate for storage
        "template_used": template_used,
        "template_id": template_id
    }

    analytics["generation_history"].insert(0, history_entry)
    analytics["generation_history"] = analytics["generation_history"][:50]

    # Save
    save_user_analytics(email, analytics)

def get_analytics_summary(email: str) -> Dict:
    """
    Get a summary of user analytics for dashboard display

    Returns:
        Dict with formatted analytics ready for display
    """
    if not email or not email.strip():
        return None

    analytics = load_user_analytics(email)

    # Calculate additional metrics
    total_gens = analytics["total_generations"]

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
        "recent_history": analytics["generation_history"][:10],
        "user_since": analytics.get("user_created", "Unknown")
    }

def get_daily_activity_chart_data(email: str, days: int = 30) -> List[Dict]:
    """
    Get daily activity data formatted for charts

    Returns:
        List of dicts with 'date' and 'count' keys for the last N days
    """
    if not email or not email.strip():
        return []

    analytics = load_user_analytics(email)
    daily_activity = analytics["daily_activity"]

    # Get last N days
    from datetime import timedelta
    today = date.today()
    date_range = [(today - timedelta(days=i)).isoformat() for i in range(days-1, -1, -1)]

    chart_data = []
    for d in date_range:
        chart_data.append({
            "date": d,
            "count": daily_activity.get(d, 0)
        })

    return chart_data

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

    analytics = load_user_analytics(email)

    # Ensure posted_tweets exists (for backward compatibility)
    if "posted_tweets" not in analytics:
        analytics["posted_tweets"] = {}

    # Store tweet info
    analytics["posted_tweets"][tweet_id] = {
        "posted_at": datetime.now().isoformat(),
        "topic": topic[:100] if topic else "",
        "tone": tone,
        "template_used": template_used,
        "metrics": {
            "likes": 0,
            "retweets": 0,
            "replies": 0,
            "views": 0,
            "bookmarks": 0
        },
        "last_fetched": None
    }

    save_user_analytics(email, analytics)

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

    analytics = load_user_analytics(email)

    if "posted_tweets" not in analytics or not analytics["posted_tweets"]:
        return 0

    refreshed_count = 0

    for tweet_id, tweet_data in analytics["posted_tweets"].items():
        metrics = fetch_tweet_metrics(email, tweet_id, client)
        if metrics:
            tweet_data["metrics"] = metrics
            tweet_data["last_fetched"] = datetime.now().isoformat()
            refreshed_count += 1

    save_user_analytics(email, analytics)
    return refreshed_count

def get_engagement_summary(email: str) -> Optional[Dict]:
    """
    Get engagement metrics summary for analytics dashboard

    Returns:
        Dict with engagement stats or None if no data
    """
    if not email or not email.strip():
        return None

    analytics = load_user_analytics(email)

    if "posted_tweets" not in analytics or not analytics["posted_tweets"]:
        return None

    posted_tweets = analytics["posted_tweets"]

    # Calculate totals
    total_likes = sum(t["metrics"]["likes"] for t in posted_tweets.values())
    total_retweets = sum(t["metrics"]["retweets"] for t in posted_tweets.values())
    total_replies = sum(t["metrics"]["replies"] for t in posted_tweets.values())
    total_views = sum(t["metrics"]["views"] for t in posted_tweets.values())
    total_bookmarks = sum(t["metrics"]["bookmarks"] for t in posted_tweets.values())

    total_posts = len(posted_tweets)
    total_engagement = total_likes + total_retweets + total_replies + total_bookmarks

    # Find best performing tweet
    best_tweet = None
    best_engagement = 0

    for tweet_id, tweet_data in posted_tweets.items():
        engagement = (
            tweet_data["metrics"]["likes"] +
            tweet_data["metrics"]["retweets"] +
            tweet_data["metrics"]["replies"] +
            tweet_data["metrics"]["bookmarks"]
        )
        if engagement > best_engagement:
            best_engagement = engagement
            best_tweet = {
                "tweet_id": tweet_id,
                "topic": tweet_data["topic"],
                "engagement": engagement,
                "metrics": tweet_data["metrics"]
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

def clear_user_analytics(email: str) -> bool:
    """
    Clear all analytics data for a user
    Useful for privacy-conscious users who want to reset their data

    Returns:
        True if data was cleared successfully, False otherwise
    """
    if not email or not email.strip():
        return False

    filepath = get_analytics_file(email)

    if not os.path.exists(filepath):
        return True  # Already clear

    try:
        os.remove(filepath)
        return True
    except Exception as e:
        print(f"Error clearing analytics: {e}")
        return False
