"""
Quick test for the clear_user_analytics function
"""

from analytics import (
    track_generation,
    get_analytics_summary,
    clear_user_analytics,
    load_user_analytics
)

def test_clear():
    test_email = "test_clear@example.com"

    print("🧪 Testing Clear Analytics Function")
    print("=" * 50)

    # Step 1: Create some test data
    print("\n1️⃣ Creating test analytics data...")
    track_generation(
        email=test_email,
        platform="X Thread",
        tone="Casual",
        length=8,
        topic="Test content"
    )

    analytics = get_analytics_summary(test_email)
    if analytics and analytics["total_generations"] > 0:
        print(f"✅ Created analytics: {analytics['total_generations']} generations")
    else:
        print("❌ Failed to create analytics")
        return

    # Step 2: Clear the data
    print("\n2️⃣ Clearing analytics data...")
    result = clear_user_analytics(test_email)

    if result:
        print("✅ Clear function returned True")
    else:
        print("❌ Clear function returned False")
        return

    # Step 3: Verify data is cleared
    print("\n3️⃣ Verifying data is cleared...")
    analytics_after = get_analytics_summary(test_email)

    if analytics_after and analytics_after["total_generations"] == 0:
        print("✅ Analytics successfully cleared!")
        print(f"   Total generations: {analytics_after['total_generations']}")
    else:
        print("❌ Analytics not cleared properly")

    print("\n" + "=" * 50)
    print("✅ Clear analytics test completed!")

if __name__ == "__main__":
    test_clear()
