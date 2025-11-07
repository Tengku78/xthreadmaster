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
        "generation_history": []
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
