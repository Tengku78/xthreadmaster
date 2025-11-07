"""
Test script for analytics module
Run this to verify analytics tracking and reporting works correctly
"""

from analytics import (
    track_generation,
    get_analytics_summary,
    get_daily_activity_chart_data,
    load_user_analytics
)
import json
from datetime import datetime, timedelta

def test_analytics():
    """Test analytics tracking with sample data"""

    test_email = "test_user@example.com"

    print("🧪 Testing Analytics Module")
    print("=" * 50)

    # Test 1: Track some sample generations
    print("\n1️⃣ Tracking sample content generations...")

    # Simulate X Thread generations
    track_generation(
        email=test_email,
        platform="X Thread",
        tone="Casual",
        length=8,
        topic="AI productivity tips",
        template_used=None,
        template_id=None
    )

    track_generation(
        email=test_email,
        platform="X Thread",
        tone="Pro",
        length=10,
        topic="SaaS marketing strategies",
        template_used="Problem-Solution Template",
        template_id="problem_solution_x"
    )

    # Simulate LinkedIn Post generation
    track_generation(
        email=test_email,
        platform="LinkedIn Post",
        tone="Pro",
        length=None,
        topic="Leadership lessons from startup",
        template_used=None,
        template_id=None
    )

    # Simulate Instagram Carousel generation
    track_generation(
        email=test_email,
        platform="Instagram Carousel",
        tone="Funny",
        length=7,
        topic="Fitness myths debunked",
        template_used=None,
        template_id=None
    )

    print("✅ Tracked 4 sample generations")

    # Test 2: Load and display analytics summary
    print("\n2️⃣ Loading analytics summary...")
    analytics = get_analytics_summary(test_email)

    if analytics:
        print(f"\n📊 Analytics Summary for {test_email}")
        print("-" * 50)
        print(f"Total Generations: {analytics['total_generations']}")
        print(f"Average per Day: {analytics['avg_per_day']}")
        print(f"Most Used Platform: {analytics['most_used_platform']}")
        print(f"Most Used Tone: {analytics['most_used_tone']}")

        print("\n🎯 Platform Breakdown:")
        for platform, count in analytics['platform_breakdown'].items():
            if count > 0:
                percentage = (count / analytics['total_generations']) * 100
                print(f"  • {platform}: {count} ({percentage:.0f}%)")

        print("\n🎨 Tone Breakdown:")
        for tone, count in analytics['tone_breakdown'].items():
            print(f"  • {tone}: {count}")

        if analytics['most_used_template']:
            print(f"\n📚 Most Used Template:")
            print(f"  • {analytics['most_used_template']['name']}: {analytics['most_used_template']['count']}x")

        print("\n⏱️ Recent Activity:")
        for entry in analytics['recent_history'][:3]:
            timestamp = datetime.fromisoformat(entry['timestamp'])
            print(f"  • {timestamp.strftime('%b %d, %I:%M %p')}: {entry['platform']} - {entry['topic'][:40]}")

        print("\n✅ Analytics summary loaded successfully")
    else:
        print("❌ Failed to load analytics summary")

    # Test 3: Get chart data
    print("\n3️⃣ Testing chart data generation...")
    chart_data = get_daily_activity_chart_data(test_email, days=7)

    if chart_data:
        print(f"✅ Generated {len(chart_data)} days of chart data")
        print("\nLast 7 days activity:")
        for entry in chart_data[-7:]:
            bars = "█" * entry['count'] if entry['count'] > 0 else "·"
            print(f"  {entry['date']}: {bars} ({entry['count']})")
    else:
        print("❌ Failed to generate chart data")

    # Test 4: View raw analytics data
    print("\n4️⃣ Raw analytics data:")
    raw_data = load_user_analytics(test_email)
    print(json.dumps({
        "total_generations": raw_data["total_generations"],
        "user_created": raw_data["user_created"],
        "last_updated": raw_data["last_updated"],
        "generations_by_platform": raw_data["generations_by_platform"],
        "generations_by_tone": raw_data["generations_by_tone"],
    }, indent=2))

    print("\n" + "=" * 50)
    print("✅ All analytics tests completed successfully!")
    print(f"\n💡 Analytics data stored in: analytics_data/")
    print(f"📁 You can find the test user data in the analytics_data directory")

if __name__ == "__main__":
    test_analytics()
