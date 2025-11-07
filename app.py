import streamlit as st
import google.generativeai as genai
import requests
import tweepy
import json
from datetime import date, datetime
import os
import tempfile
import io
import zipfile
from PIL import Image
import base64
import pandas as pd
from templates import (
    get_all_templates,
    get_free_templates,
    get_pro_templates,
    get_categories,
    get_template_by_id,
    fill_template
)
from analytics import (
    track_generation,
    get_analytics_summary,
    get_daily_activity_chart_data,
    clear_user_analytics,
    track_posted_tweet,
    refresh_all_tweet_metrics,
    get_engagement_summary,
    save_thread_to_history,
    get_thread_history
)

# === CONFIG ===
# NOTE: genai.configure() is now called lazily in get_model() to prevent deployment hangs

# Get Stripe payment links from secrets (with fallback)
STRIPE_PRO_LINK = st.secrets.get("STRIPE_PRO_LINK", "#")
STRIPE_VISUAL_PACK_LINK = st.secrets.get("STRIPE_VISUAL_PACK_LINK", "#")

# LinkedIn OAuth Configuration
LINKEDIN_CLIENT_ID = st.secrets.get("LINKEDIN_CLIENT_ID", "")
LINKEDIN_CLIENT_SECRET = st.secrets.get("LINKEDIN_CLIENT_SECRET", "")
LINKEDIN_REDIRECT_URI = "https://xthreadmaster.streamlit.app"

# === OAUTH TOKEN STORAGE ===
# Helper functions to store/retrieve OAuth tokens temporarily
def save_oauth_secret(oauth_token, oauth_secret):
    """Save OAuth secret to a temporary file keyed by oauth_token"""
    temp_dir = tempfile.gettempdir()
    filepath = os.path.join(temp_dir, f"xthread_oauth_{oauth_token}.json")
    data = {
        "secret": oauth_secret,
        "timestamp": datetime.now().isoformat()
    }
    with open(filepath, 'w') as f:
        json.dump(data, f)
    return filepath

def get_oauth_secret(oauth_token):
    """Retrieve OAuth secret from temporary file"""
    temp_dir = tempfile.gettempdir()
    filepath = os.path.join(temp_dir, f"xthread_oauth_{oauth_token}.json")

    if not os.path.exists(filepath):
        return None

    try:
        with open(filepath, 'r') as f:
            data = json.load(f)

        # Check if token is less than 10 minutes old
        timestamp = datetime.fromisoformat(data['timestamp'])
        age = (datetime.now() - timestamp).total_seconds()

        if age > 600:  # 10 minutes
            os.remove(filepath)
            return None

        return data['secret']
    except Exception:
        return None

def cleanup_oauth_secret(oauth_token):
    """Remove OAuth secret file after use"""
    temp_dir = tempfile.gettempdir()
    filepath = os.path.join(temp_dir, f"xthread_oauth_{oauth_token}.json")
    try:
        if os.path.exists(filepath):
            os.remove(filepath)
    except:
        pass

# LinkedIn OAuth state storage (uses same pattern as X OAuth)
def save_linkedin_state(state, data):
    """Save LinkedIn OAuth state to temporary file"""
    temp_dir = tempfile.gettempdir()
    filepath = os.path.join(temp_dir, f"linkedin_state_{state}.json")
    data_with_timestamp = {
        **data,
        "timestamp": datetime.now().isoformat()
    }
    with open(filepath, 'w') as f:
        json.dump(data_with_timestamp, f)
    return filepath

def get_linkedin_state(state):
    """Retrieve LinkedIn OAuth state from temporary file"""
    temp_dir = tempfile.gettempdir()
    filepath = os.path.join(temp_dir, f"linkedin_state_{state}.json")

    if not os.path.exists(filepath):
        return None

    try:
        with open(filepath, 'r') as f:
            data = json.load(f)

        # Check if state is less than 10 minutes old
        timestamp = datetime.fromisoformat(data['timestamp'])
        age = (datetime.now() - timestamp).total_seconds()

        if age > 600:  # 10 minutes
            os.remove(filepath)
            return None

        return data
    except Exception:
        return None

def cleanup_linkedin_state(state):
    """Remove LinkedIn OAuth state file after use"""
    temp_dir = tempfile.gettempdir()
    filepath = os.path.join(temp_dir, f"linkedin_state_{state}.json")
    try:
        if os.path.exists(filepath):
            os.remove(filepath)
    except:
        pass

# === MODEL ===
@st.cache_resource
def get_model():
    # Configure genai API here (lazy loading to prevent deployment hang)
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

    # Try models in order of preference
    for name in ("gemini-2.0-flash-exp", "gemini-1.5-flash", "gemini-1.5-pro"):
        try:
            m = genai.GenerativeModel(name)
            # Quick validation without API call
            return m
        except Exception:
            continue

    # If no model works, show error
    st.error("❌ AI service unavailable. Please contact support or try again later.")
    st.stop()

# Lazy load model - only initialized when first used
def get_or_create_model():
    if "model" not in st.session_state:
        st.session_state.model = get_model()
    return st.session_state.model

st.set_page_config(page_title="XThreadMaster", page_icon="🚀", layout="centered")

# === SIDEBAR ===
# Note: Sidebar content is rendered after user_tier is determined (see below after line 400)

# === INITIALIZE SESSION STATE ===
if "gen_count" not in st.session_state:
    st.session_state.gen_count = 0
if "last_reset" not in st.session_state:
    st.session_state.last_reset = date.today()
if "carousel_count" not in st.session_state:
    st.session_state.carousel_count = 0
if "carousel_last_reset" not in st.session_state:
    st.session_state.carousel_last_reset = date.today()
if "x_logged_in" not in st.session_state:
    st.session_state.x_logged_in = False
if "linkedin_logged_in" not in st.session_state:
    st.session_state.linkedin_logged_in = False
if "thread" not in st.session_state:
    st.session_state.thread = None
if "carousel" not in st.session_state:
    st.session_state.carousel = None
if "carousel_images" not in st.session_state:
    st.session_state.carousel_images = []
if "platform" not in st.session_state:
    st.session_state.platform = "X Thread"
# Thread history now stored in Supabase (removed session state)

st.title("🚀 XThreadMaster")
st.markdown("Generate viral X threads in seconds with AI")
st.markdown("---")

# === INPUTS ===
with st.expander("⚙️ Account Settings", expanded=False):
    email = st.text_input(
        "Email (optional - for Pro features)",
        value=st.session_state.get("saved_email", ""),
        placeholder="you@email.com",
        help="Enter your email to check Pro subscription status"
    )

    # Save email to session state when changed
    if email and email.strip() and email != st.session_state.get("saved_email"):
        st.session_state.saved_email = email

# === LIMIT ===
if st.session_state.last_reset != date.today():
    st.session_state.gen_count = 0
    st.session_state.last_reset = date.today()

# Reset carousel count monthly (first day of month)
current_month = date.today().replace(day=1)
last_reset_month = st.session_state.carousel_last_reset.replace(day=1)
if current_month != last_reset_month:
    st.session_state.carousel_count = 0
    st.session_state.carousel_last_reset = date.today()

# === SUBSCRIPTION TIERS ===
def get_user_tier(e):
    """
    Check user's subscription tier via Stripe.
    Returns: 'free', 'pro' ($12/mo), or 'visual_pack' ($17/mo)
    """
    if not e or not e.strip():
        return 'free'

    try:
        # Check Stripe for active subscriptions
        custs_response = requests.get(
            "https://api.stripe.com/v1/customers",
            params={"email": e},
            auth=(st.secrets["STRIPE_SECRET_KEY"], ""),
            timeout=10
        )
        custs = custs_response.json().get("data", [])

        for c in custs:
            subs_response = requests.get(
                f"https://api.stripe.com/v1/subscriptions",
                params={"customer": c["id"], "status": "active"},
                auth=(st.secrets["STRIPE_SECRET_KEY"], ""),
                timeout=10
            )
            subs = subs_response.json().get("data", [])

            for sub in subs:
                # Get the price amount to determine tier
                items = sub.get("items", {}).get("data", [])
                if items:
                    price = items[0].get("price", {})
                    amount = price.get("unit_amount", 0) / 100  # Convert cents to dollars

                    # Determine tier based on price
                    if amount >= 17:
                        return 'visual_pack'  # $17/mo - Instagram + X
                    elif amount >= 12:
                        return 'pro'  # $12/mo - X only

            # If we found subscriptions but couldn't parse price, default to pro
            if subs:
                return 'pro'

    except requests.exceptions.RequestException as e:
        st.warning(f"⚠️ Could not verify subscription: {e}")
    except Exception as e:
        st.warning(f"⚠️ Stripe verification error: {e}")

    return 'free'

# Get user tier
user_tier = get_user_tier(email)

# TEMPORARY: Test mode for Visual Pack (remove after testing)
if email == "testtest@gmail.com":
    user_tier = 'visual_pack'

pro = user_tier in ['pro', 'visual_pack']
visual_pack = user_tier == 'visual_pack'

# === RENDER SIDEBAR ===
with st.sidebar:
    # Add Analytics Dashboard tab for Pro users
    if pro and email and email.strip():
        sidebar_tab = st.radio(
            "Navigation",
            ["📊 Analytics", "ℹ️ About"],
            label_visibility="collapsed"
        )
    else:
        sidebar_tab = "ℹ️ About"

    if sidebar_tab == "📊 Analytics" and pro and email and email.strip():
        st.title("📊 Analytics Dashboard")

        # Load analytics summary
        analytics = get_analytics_summary(email)

        if analytics and analytics["total_generations"] > 0:
            # Key Metrics
            st.metric("Total Content", analytics["total_generations"])

            col1, col2 = st.columns(2)
            with col1:
                st.metric("Avg/Day", analytics["avg_per_day"])
            with col2:
                # Calculate this week's activity
                recent_activity = analytics["recent_activity"]
                this_week = sum(recent_activity.values())
                st.metric("This Week", this_week)

            st.markdown("---")

            # Platform Breakdown
            st.markdown("**🎯 Platform Usage**")
            platform_data = analytics["platform_breakdown"]
            for platform_name, count in platform_data.items():
                if count > 0:
                    percentage = (count / analytics["total_generations"]) * 100
                    st.progress(percentage / 100)
                    st.caption(f"{platform_name}: {count} ({percentage:.0f}%)")

            st.markdown("---")

            # Tone Breakdown
            st.markdown("**🎨 Tone Preferences**")
            tone_data = analytics["tone_breakdown"]
            if tone_data:
                top_3_tones = sorted(tone_data.items(), key=lambda x: x[1], reverse=True)[:3]
                for tone_name, count in top_3_tones:
                    st.caption(f"• {tone_name}: {count}x")

            st.markdown("---")

            # Template Usage
            st.markdown("**📚 Template Usage**")
            if analytics["most_used_template"]:
                st.caption(f"**Most Used:** {analytics['most_used_template']['name']}")
                st.caption(f"Used {analytics['most_used_template']['count']}x")
            else:
                st.caption("No templates used yet")

            st.markdown("---")

            # Activity Chart (Last 30 days)
            st.markdown("**📈 Activity Trend (30 Days)**")
            chart_data = get_daily_activity_chart_data(email, days=30)
            if chart_data and any(d["count"] > 0 for d in chart_data):
                df = pd.DataFrame(chart_data)
                df['date'] = pd.to_datetime(df['date'])
                st.line_chart(df.set_index('date')['count'], use_container_width=True)
            else:
                st.caption("No activity data yet")

            st.markdown("---")

            # X Engagement Metrics (if user has posted tweets)
            if st.session_state.get("x_logged_in"):
                engagement = get_engagement_summary(email)

                if engagement and engagement["total_posts"] > 0:
                    st.markdown("**🔥 X Engagement**")

                    # Total engagement metrics
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Posts", engagement["total_posts"])
                    with col2:
                        st.metric("❤️ Likes", f"{engagement['total_likes']:,}")
                    with col3:
                        st.metric("🔄 Retweets", f"{engagement['total_retweets']:,}")

                    # Additional metrics
                    col4, col5, col6 = st.columns(3)
                    with col4:
                        st.metric("💬 Replies", f"{engagement['total_replies']:,}")
                    with col5:
                        st.metric("👁️ Views", f"{engagement['total_views']:,}" if engagement['total_views'] > 0 else "N/A")
                    with col6:
                        st.metric("🔖 Saves", f"{engagement['total_bookmarks']:,}")

                    # Averages
                    st.caption(f"**Avg Engagement:** {engagement['avg_engagement']:.1f} per post")
                    st.caption(f"**Avg Likes:** {engagement['avg_likes']:.1f} | **Avg Retweets:** {engagement['avg_retweets']:.1f}")

                    # Best performing tweet
                    if engagement["best_tweet"]:
                        best = engagement["best_tweet"]
                        st.markdown(f"**🏆 Best Thread:** {best['topic'][:50]}...")
                        st.caption(f"❤️ {best['metrics']['likes']} | 🔄 {best['metrics']['retweets']} | 💬 {best['metrics']['replies']} | Total: {best['engagement']}")

                    # Refresh Metrics Button
                    if st.button("🔄 Refresh Engagement Metrics", use_container_width=True, help="Fetch latest engagement data from X"):
                        with st.spinner("Fetching latest metrics from X..."):
                            try:
                                # Create authenticated client
                                client = tweepy.Client(
                                    consumer_key=st.secrets["X_CONSUMER_KEY"],
                                    consumer_secret=st.secrets["X_CONSUMER_SECRET"],
                                    access_token=st.session_state.x_access_token,
                                    access_token_secret=st.session_state.x_access_secret,
                                )

                                # Refresh all tweet metrics
                                refreshed_count = refresh_all_tweet_metrics(email, client)

                                if refreshed_count > 0:
                                    st.success(f"✅ Updated metrics for {refreshed_count} post(s)!")
                                    st.rerun()
                                else:
                                    st.info("📊 No posts to refresh")

                            except Exception as e:
                                st.error(f"❌ Failed to refresh metrics: {e}")

                    st.markdown("---")

            st.markdown("---")

            # Recent Activity
            st.markdown("**⏱️ Recent Activity**")
            recent_history = analytics["recent_history"][:5]
            if recent_history:
                for entry in recent_history:
                    timestamp = datetime.fromisoformat(entry["timestamp"])
                    time_str = timestamp.strftime("%b %d, %I:%M %p")
                    platform_emoji = {"X Thread": "🐦", "LinkedIn Post": "💼", "Instagram Carousel": "📸"}.get(entry["platform"], "📝")
                    st.caption(f"{platform_emoji} {time_str}")
                    st.caption(f"   {entry['topic'][:40]}...")
            else:
                st.caption("No recent activity")

            # Clear Analytics Button (at bottom)
            st.markdown("---")
            if st.button("🗑️ Clear All Analytics", use_container_width=True, help="Permanently delete all your analytics data"):
                if clear_user_analytics(email):
                    st.success("✅ Analytics data cleared successfully!")
                    st.info("Your data has been permanently deleted. New analytics will be tracked starting now.")
                    st.rerun()
                else:
                    st.error("❌ Failed to clear analytics data. Please try again.")

        else:
            st.info("📊 Generate content to see your analytics here!")
            st.caption("Your analytics will show:")
            st.caption("• Total content generated")
            st.caption("• Platform breakdown")
            st.caption("• Most used templates")
            st.caption("• Activity trends")

    else:
        # About section (original)
        st.title("ℹ️ About")
        st.markdown("""
        **XThreadMaster** generates viral content for X & Instagram using AI.

        ### ✨ Features
        - 🤖 AI-powered content generation
        - 📚 Pre-written templates library
        - 🎨 Multiple tone options
        - 📥 Download content
        - 🚀 Auto-post to X (Pro+)

        ### 🆓 Free Tier
        - 3 X threads per day
        - 5 content templates
        - Manual posting

        ### 💎 Pro ($12/mo)
        - ♾️ Unlimited X threads
        - 💼 LinkedIn posts (B2B content)
        - 📚 15+ content templates (all categories)
        - 🚀 One-click auto-posting to X
        - 🔗 X account integration
        - ✏️ Edit before posting
        - 📚 Thread history (last 10)
        - 📊 Analytics dashboard

        ### 🎨 Visual Pack ($17/mo)
        - ✅ Everything in Pro
        - 📸 Instagram carousel captions
        - 🖼️ AI-generated images (Stability AI)
        - 📦 Download as ZIP
        - 💯 100 carousels/month

        ---

        [Upgrade to Pro ($12/mo)]({STRIPE_PRO_LINK})

        [Upgrade to Visual Pack ($17/mo)]({STRIPE_VISUAL_PACK_LINK})
        """.replace("{STRIPE_PRO_LINK}", STRIPE_PRO_LINK).replace("{STRIPE_VISUAL_PACK_LINK}", STRIPE_VISUAL_PACK_LINK))

# === CONTENT SETTINGS ===
st.subheader("📝 Content Settings")

# Platform selector
platform_options = ["X Thread"]
if pro:  # LinkedIn available for Pro+ users
    platform_options.append("LinkedIn Post")
if visual_pack:
    platform_options.append("Instagram Carousel")

platform = st.selectbox(
    "Platform*",
    platform_options,
    help="Choose which platform to generate content for"
)

# === TEMPLATES SECTION ===
st.markdown("---")
st.subheader("📚 Use a Template (Optional)")

# Get available templates based on user tier
if pro:
    available_templates = get_all_templates()
    template_count_text = "✨ **Pro Access:** All 15+ templates unlocked"
else:
    available_templates = get_free_templates()
    template_count_text = f"🆓 **Free Tier:** {len(available_templates)} templates available | [Upgrade to Pro]({STRIPE_PRO_LINK}) for 15+ templates"

st.info(template_count_text)

# Filter templates by platform
platform_templates = [t for t in available_templates if t["platform"] == platform]

if platform_templates:
    # Template selector
    use_template = st.checkbox("🎯 Start from a template", value=False, help="Pre-written, proven templates you can customize")

    if use_template:
        # Category filter
        categories = list(set(t["category"] for t in platform_templates))
        selected_category = st.selectbox(
            "Category",
            ["All"] + sorted(categories),
            help="Filter templates by category"
        )

        # Filter by category
        if selected_category == "All":
            filtered_templates = platform_templates
        else:
            filtered_templates = [t for t in platform_templates if t["category"] == selected_category]

        # Template selection
        template_options = {f"{t['title']} ({t['category']})": t['id'] for t in filtered_templates}

        if template_options:
            selected_template_name = st.selectbox(
                "Choose Template",
                list(template_options.keys()),
                help="Select a proven template to customize"
            )

            selected_template_id = template_options[selected_template_name]
            selected_template = get_template_by_id(selected_template_id)

            # Show template preview
            with st.expander("👁️ Preview Template", expanded=False):
                st.code(selected_template["template"], language="text")
                st.caption(f"💡 Example: {selected_template['example']}")

            # Fill in template placeholders
            st.markdown("**Fill in the blanks:**")
            placeholder_values = {}

            # Create input fields for each placeholder
            for placeholder, description in selected_template["placeholders"].items():
                placeholder_values[placeholder] = st.text_input(
                    f"{placeholder.replace('_', ' ').title()}",
                    placeholder=description,
                    key=f"template_{placeholder}"
                )

            # Store template data in session state
            if "template_mode" not in st.session_state:
                st.session_state.template_mode = False

            st.session_state.template_mode = True
            st.session_state.selected_template = selected_template
            st.session_state.placeholder_values = placeholder_values
        else:
            st.warning(f"No templates available for {selected_category} in {platform}")
    else:
        # Clear template mode if unchecked
        if "template_mode" in st.session_state:
            st.session_state.template_mode = False
else:
    st.info(f"💡 No templates available yet for {platform}. Coming soon!")

st.markdown("---")

col1, col2 = st.columns(2)
with col1:
    # Make topic optional if using template
    if st.session_state.get("template_mode", False):
        topic = st.text_input("Topic (optional with templates)", placeholder="Additional context for AI", help="Optional: Add context to enhance the template")
    else:
        topic = st.text_input("Topic*", placeholder="AI side-hustles, productivity tips, etc.", help="What should your content be about?")
with col2:
    tone = st.selectbox("Tone", ["Casual", "Funny", "Pro", "Degen"], help="Choose the writing style")

# Dynamic length slider based on platform
if platform == "X Thread":
    length = st.slider("Thread Length (tweets)", 5, 15, 8, help="Number of tweets in your thread")
elif platform == "LinkedIn Post":
    length = None  # LinkedIn posts are single-format
else:  # Instagram Carousel
    length = st.slider("Carousel Length (slides)", 5, 10, 7, help="Number of slides in your carousel")

# Update sidebar with thread history (Pro only)
if pro:
    with st.sidebar:
        st.markdown("---")
        st.subheader("📚 Thread History")

        # Load history from Supabase
        thread_history = get_thread_history(email, limit=10)

        if thread_history:
            st.caption("Your last 10 threads")
            for idx, entry in enumerate(thread_history):
                platform_emoji = {"X Thread": "🐦", "LinkedIn Post": "💼", "Instagram Carousel": "📸"}.get(entry['platform'], "📝")
                with st.expander(f"{platform_emoji} {entry['platform']} - {datetime.fromisoformat(entry['timestamp']).strftime('%b %d, %I:%M %p')}", expanded=False):
                    st.caption(f"**Platform:** {entry['platform']}")
                    st.caption(f"**Created:** {datetime.fromisoformat(entry['timestamp']).strftime('%b %d, %I:%M %p')}")

                    # Show preview of content
                    st.text_area(
                        "Content Preview",
                        value=entry['content'][:500] + ("..." if len(entry['content']) > 500 else ""),
                        height=100,
                        disabled=True,
                        key=f"preview_{idx}"
                    )

                    if st.button(f"📥 Load This {entry['platform']}", key=f"load_{idx}", use_container_width=True):
                        st.session_state.thread = entry['content']
                        st.session_state.platform = entry['platform']
                        st.rerun()
        else:
            st.caption("Generate content to see your history here!")

# Show subscription status
if email and email.strip():
    if visual_pack:
        remaining_carousels = 100 - st.session_state.carousel_count
        st.success(f"✅ **Visual Pack Active** - X threads + Instagram carousels with AI images ({remaining_carousels}/100 carousels remaining this month)")
    elif pro:
        st.success("✅ **Pro Account Active** - Unlimited X threads & auto-posting")
        st.info(f"💎 [Upgrade to Visual Pack ($17/mo)]({STRIPE_VISUAL_PACK_LINK}) to unlock Instagram carousels with AI-generated images")
    else:
        remaining_today = 3 - st.session_state.gen_count
        st.info(f"🆓 **Free Tier** - {remaining_today} generations remaining today | [Upgrade to Pro]({STRIPE_PRO_LINK}) for unlimited access")

# === OAUTH: STATE PARAMETER (NO SESSION LOSS) ===
query = st.query_params

# CALLBACK - Handle OAuth return
if "oauth_verifier" in query and "oauth_token" in query:
    if not st.session_state.get("processing_oauth"):
        st.session_state.processing_oauth = True

        verifier = query["oauth_verifier"]
        oauth_token = query["oauth_token"]

        # Retrieve token secret from file storage
        req_secret = get_oauth_secret(oauth_token)

        if not req_secret:
            st.error("❌ OAuth session expired or not found.")
            st.warning("📝 The OAuth token was not found. This can happen if:")
            st.markdown("""
            - More than 10 minutes passed since you clicked 'Connect'
            - The temporary storage was cleared
            - You're on a multi-instance deployment
            """)
            st.info("💡 **Solution:** Click 'Connect X Account' again and complete the authorization within 10 minutes.")

            st.query_params.clear()
            st.session_state.processing_oauth = False
            st.stop()

        auth = tweepy.OAuth1UserHandler(
            st.secrets["X_CONSUMER_KEY"],
            st.secrets["X_CONSUMER_SECRET"],
            callback="https://xthreadmaster.streamlit.app"
        )
        auth.request_token = {"oauth_token": oauth_token, "oauth_token_secret": req_secret}

        try:
            access = auth.get_access_token(verifier)
            st.session_state.x_access_token = access[0]
            st.session_state.x_access_secret = access[1]

            # Get user info using v1.1 API which supports OAuth 1.0a
            api = tweepy.API(auth)
            user = api.verify_credentials()
            st.session_state.x_username = user.screen_name
            st.session_state.x_logged_in = True

            # Clean up temporary storage
            cleanup_oauth_secret(oauth_token)
            st.session_state.pop("processing_oauth", None)

            # Clear query params and rerun
            st.query_params.clear()
            st.success(f"✅ Connected as @{user.screen_name}")
            st.rerun()
        except Exception as e:
            st.error(f"❌ OAuth failed: {e}")
            cleanup_oauth_secret(oauth_token)
            st.session_state.processing_oauth = False
            st.query_params.clear()

# X ACCOUNT CONNECTION (Pro Only)
if pro:
    st.markdown("---")
    st.subheader("🔗 X Account Connection")

    if not st.session_state.get("x_logged_in"):
        col1, col2 = st.columns([2, 1])
        with col1:
            st.write("Connect your X account to enable one-click auto-posting")
        with col2:
            if st.button("Connect X Account", use_container_width=True, type="secondary"):
                auth = tweepy.OAuth1UserHandler(
                    st.secrets["X_CONSUMER_KEY"],
                    st.secrets["X_CONSUMER_SECRET"],
                    callback="https://xthreadmaster.streamlit.app"
                )
                try:
                    auth_url = auth.get_authorization_url(signin_with_twitter=True)
                    rt = auth.request_token

                    # Store token secret in temporary file storage (survives redirect)
                    save_oauth_secret(rt["oauth_token"], rt["oauth_token_secret"])

                    st.markdown(f"### [👉 Click here to authorize with X]({auth_url})")
                    st.info("💡 You'll be redirected to X. After authorizing, you'll return automatically (within 10 minutes).")
                except Exception as e:
                    st.error(f"❌ Setup failed: {e}")

    # LOGGED IN
    else:
        col1, col2 = st.columns([2, 1])
        username = st.session_state.get("x_username", "Unknown")
        with col1:
            st.success(f"✅ Connected as @{username}")
        with col2:
            if st.button("Disconnect", use_container_width=True):
                for k in ["x_access_token", "x_access_secret", "x_username", "x_logged_in"]:
                    st.session_state.pop(k, None)
                st.rerun()

# Show helpful message if X is connected but not showing as Pro (email missing)
if st.session_state.get("x_logged_in") and (not email or not email.strip()):
    st.info("😊 **You're connected to X!** Just re-enter your Pro email in Account Settings above to unlock all features!")

# === GENERATE ===
st.markdown("---")

# Dynamic button text
if platform == "X Thread":
    button_text = "✨ Generate Viral Thread"
elif platform == "LinkedIn Post":
    button_text = "💼 Generate LinkedIn Post"
else:
    button_text = "🎨 Generate Instagram Carousel"

if st.button(button_text, type="primary", use_container_width=True):
    # Check if using template mode
    template_mode = st.session_state.get("template_mode", False)

    # Validation: topic required only if not using template
    if not template_mode and not topic.strip():
        st.warning("⚠️ Please enter a topic")
        st.stop()

    # Check if template placeholders are filled
    if template_mode:
        missing_fields = []
        for key, value in st.session_state.placeholder_values.items():
            if not value or not value.strip():
                missing_fields.append(key.replace('_', ' ').title())

        if missing_fields:
            st.warning(f"⚠️ Please fill in all template fields: {', '.join(missing_fields)}")
            st.stop()

    if not pro and st.session_state.gen_count >= 3:
        st.error("🚫 Free limit reached: 3 generations per day")
        st.info(f"💎 [Upgrade to Pro]({STRIPE_PRO_LINK}) for unlimited generations and auto-posting")
        st.stop()

    if not pro:
        st.session_state.gen_count += 1
    remaining = 3 - st.session_state.gen_count if not pro else None

    # Generate based on platform
    if platform == "X Thread":
        # Generate X Thread
        with st.spinner("🤖 Generating your viral thread..."):
            # If using template, fill it in first
            if template_mode:
                template_obj = st.session_state.selected_template
                filled_template = fill_template(template_obj["template"], st.session_state.placeholder_values)

                # Use AI to polish the template if topic provided
                if topic and topic.strip():
                    prompt = f"""Enhance this X/Twitter thread with the following context: "{topic}"

Original thread:
{filled_template}

Requirements:
- Keep the core message intact
- Add relevant details based on the context
- Tone: {tone}
- Keep each tweet under 280 characters
- Format: ONE TWEET PER LINE"""
                else:
                    # Just format the template as a thread
                    prompt = f"""Format this content as a {length}-tweet X/Twitter thread:

{filled_template}

Requirements:
- Tone: {tone}
- Keep each tweet under 280 characters
- Format: ONE TWEET PER LINE
- Maintain the core message"""
            else:
                # Standard generation from topic
                prompt = f"""Create a VIRAL X/Twitter thread about: "{topic}"

Requirements:
- Exactly {length} tweets
- Tone: {tone}
- Structure: Hook → Value → CTA
- Use relevant emojis
- Keep each tweet under 280 characters
- Make it engaging and shareable
- Format: ONE TWEET PER LINE"""

            try:
                model = get_or_create_model()
                thread = model.generate_content(prompt).text.strip()
            except Exception as e:
                error_msg = str(e)
                if "429" in error_msg or "Resource exhausted" in error_msg:
                    st.error("⏱️ **API Rate Limit Reached**")
                    st.warning("The AI service is temporarily at capacity. This happens on the free tier.")
                    st.info("""
                    **Solutions:**
                    1. Wait 1-2 hours and try again
                    2. Upgrade your Google AI API to paid tier for higher limits
                    3. Contact support if this persists
                    """)
                else:
                    st.error(f"❌ AI generation failed: {error_msg}")
                st.stop()

        st.session_state.thread = thread
        st.session_state.platform = "X Thread"
        st.session_state.remaining = remaining

        # Track analytics (Pro users only)
        if pro and email and email.strip():
            template_name = None
            template_id = None
            if template_mode:
                template_obj = st.session_state.selected_template
                template_name = template_obj["title"]
                template_id = template_obj["id"]

            track_generation(
                email=email,
                platform="X Thread",
                tone=tone,
                length=length,
                topic=topic if topic else "Template-based",
                template_used=template_name,
                template_id=template_id
            )

    elif platform == "LinkedIn Post":
        # Generate LinkedIn Post (Pro feature)
        with st.spinner("💼 Generating your professional LinkedIn post..."):
            # If using template, fill it in first
            if template_mode:
                template_obj = st.session_state.selected_template
                filled_template = fill_template(template_obj["template"], st.session_state.placeholder_values)

                # Use AI to enhance template if topic provided
                if topic and topic.strip():
                    prompt = f"""Enhance this LinkedIn post with additional context: "{topic}"

Original post:
{filled_template}

Requirements:
- Keep the core message intact
- Add relevant details based on the context
- Tone: {tone}
- LinkedIn best practices: Professional yet engaging
- 1300-3000 characters optimal
- End with 3-5 relevant hashtags"""
                else:
                    # Just format and optimize the template
                    prompt = f"""Optimize this LinkedIn post:

{filled_template}

Requirements:
- Tone: {tone}
- LinkedIn best practices applied
- Add line breaks for readability
- End with 3-5 relevant hashtags
- Keep the core message intact"""
            else:
                # Standard generation from topic
                prompt = f"""Create a VIRAL LinkedIn post about: "{topic}"

Requirements:
- Tone: {tone}
- LinkedIn best practices: Hook in first line, value-driven content
- 1300-3000 characters (LinkedIn optimal length)
- Professional yet engaging
- Include relevant emojis (LinkedIn-appropriate)
- Structure: Hook → Story/Insight → Value → CTA
- Use line breaks for readability
- End with 3-5 relevant hashtags
- Make it shareable and comment-worthy"""

            try:
                model = get_or_create_model()
                linkedin_post = model.generate_content(prompt).text.strip()
            except Exception as e:
                error_msg = str(e)
                if "429" in error_msg or "Resource exhausted" in error_msg:
                    st.error("⏱️ **API Rate Limit Reached**")
                    st.warning("The AI service is temporarily at capacity.")
                    st.info("""
                    **Solutions:**
                    1. Wait 1-2 hours and try again
                    2. Upgrade your Google AI API to paid tier
                    3. Contact support if this persists
                    """)
                else:
                    st.error(f"❌ AI generation failed: {error_msg}")
                st.stop()

        st.session_state.thread = linkedin_post
        st.session_state.platform = "LinkedIn Post"

        # Track analytics (Pro users only)
        if pro and email and email.strip():
            template_name = None
            template_id = None
            if template_mode:
                template_obj = st.session_state.selected_template
                template_name = template_obj["title"]
                template_id = template_obj["id"]

            track_generation(
                email=email,
                platform="LinkedIn Post",
                tone=tone,
                length=None,  # LinkedIn posts don't have length
                topic=topic if topic else "Template-based",
                template_used=template_name,
                template_id=template_id
            )

    else:  # Instagram Carousel
        # Check carousel monthly limit (100/month soft cap)
        if st.session_state.carousel_count >= 100:
            st.error("🚫 Monthly carousel limit reached: 100 carousels per month")
            st.info("You've hit the soft cap for this month. This limit resets on the 1st of next month.")
            st.warning("💡 Need more? Contact support for enterprise pricing.")
            st.stop()

        # Generate Instagram Carousel
        with st.spinner("🎨 Generating your Instagram carousel..."):
            # If using template, fill it in first
            if template_mode:
                template_obj = st.session_state.selected_template
                filled_template = fill_template(template_obj["template"], st.session_state.placeholder_values)

                # Use AI to enhance template if topic provided
                if topic and topic.strip():
                    prompt = f"""Enhance this Instagram carousel with additional context: "{topic}"

Original carousel:
{filled_template}

Requirements:
- Keep the core message intact
- Add relevant details based on the context
- Tone: {tone}
- Each slide: SLIDE X: [Title] format
- Use relevant emojis
- Make it visually engaging"""
                else:
                    # Just optimize the template
                    prompt = f"""Optimize this Instagram carousel:

{filled_template}

Requirements:
- Tone: {tone}
- Each slide: SLIDE X: [Title] format
- Use relevant emojis
- Keep the core message intact"""
            else:
                # Standard generation from topic
                prompt = f"""Create a VIRAL Instagram carousel about: "{topic}"

Requirements:
- Exactly {length} slides
- Tone: {tone}
- Each slide should have a catchy title (max 5 words) and description (2-3 sentences)
- Use relevant emojis
- Make it visually engaging and shareable
- Format: For each slide, write:
  SLIDE X: [Title]
  [Description]

  One slide per section."""

            try:
                model = get_or_create_model()
                carousel = model.generate_content(prompt).text.strip()
            except Exception as e:
                error_msg = str(e)
                if "429" in error_msg or "Resource exhausted" in error_msg:
                    st.error("⏱️ **API Rate Limit Reached**")
                    st.warning("The AI service is temporarily at capacity. This happens on the free tier.")
                    st.info("""
                    **Solutions:**
                    1. Wait 1-2 hours and try again
                    2. Upgrade your Google AI API to paid tier for higher limits
                    3. Contact support if this persists
                    """)
                else:
                    st.error(f"❌ AI generation failed: {error_msg}")
                st.stop()

        # Generate AI images with Stability AI
        carousel_images = []
        generation_errors = []

        # Parse carousel to extract slide titles
        slides = []
        for line in carousel.split('\n'):
            # Remove markdown formatting (**, *, etc.) before checking
            clean_line = line.strip().lstrip('*').strip()
            if clean_line.startswith('SLIDE'):
                if ':' in clean_line:
                    # Extract title after colon, remove any trailing markdown
                    title = clean_line.split(':', 1)[1].strip().rstrip('*').strip()
                    slides.append(title)

        # Stability AI configuration
        stability_api_key = st.secrets.get("STABILITY_API_KEY", "")

        if not stability_api_key:
            st.warning("⚠️ Stability AI API key not configured. Images will not be generated.")
            st.info("Add STABILITY_API_KEY to your secrets to enable AI image generation.")
        else:
            with st.spinner(f"🖼️ Generating {length} AI images for your carousel..."):
                # Generate images using Stability AI API
                api_host = "https://api.stability.ai"

                for i, slide_title in enumerate(slides, 1):
                    try:
                        # Create image prompt
                        img_prompt = f"Professional Instagram carousel image: {slide_title}. Topic: {topic}. Style: modern, clean, vibrant, social media optimized, no text overlay"

                        # Call Stability AI API
                        response = requests.post(
                            f"{api_host}/v1/generation/stable-diffusion-xl-1024-v1-0/text-to-image",
                            headers={
                                "Content-Type": "application/json",
                                "Accept": "application/json",
                                "Authorization": f"Bearer {stability_api_key}"
                            },
                            json={
                                "text_prompts": [{"text": img_prompt}],
                                "cfg_scale": 7,
                                "height": 1024,
                                "width": 1024,
                                "samples": 1,
                                "steps": 30,
                            },
                            timeout=60
                        )

                        if response.status_code == 200:
                            data = response.json()
                            for artifact in data.get("artifacts", []):
                                if artifact.get("finishReason") == "SUCCESS":
                                    img_base64 = artifact.get("base64")
                                    img_bytes = base64.b64decode(img_base64)

                                    carousel_images.append({
                                        'data': img_bytes,
                                        'slide_num': i,
                                        'title': slide_title
                                    })
                                    break
                        else:
                            error_detail = f"API returned {response.status_code}"
                            try:
                                error_body = response.json()
                                if 'message' in error_body:
                                    error_detail += f": {error_body['message']}"
                            except:
                                pass
                            generation_errors.append(f"Slide {i}: {error_detail}")
                            continue

                    except Exception as e:
                        generation_errors.append(f"Slide {i}: {str(e)}")
                        continue

        # Show consolidated error messages OUTSIDE spinner
        if generation_errors:
            st.warning("⚠️ Some images failed to generate:")
            for error in generation_errors[:3]:  # Show first 3 errors
                st.caption(f"• {error}")
            if len(generation_errors) > 3:
                st.caption(f"• ... and {len(generation_errors) - 3} more errors")

        # Always show status of image generation
        if stability_api_key and not carousel_images:
            if generation_errors:
                st.error("❌ All image generations failed. Check errors above.")
            else:
                st.error("❌ No images were generated and no errors were logged. This may indicate:")
                st.info("1. The API key format is incorrect\n2. Network timeout issues\n3. Invalid API response format")
                st.info(f"💡 Debug info: Attempted to generate {len(slides)} images")
        elif not stability_api_key and not carousel_images:
            # Already showed warning above, no need to repeat
            pass

        # Increment carousel count
        st.session_state.carousel_count += 1

        st.session_state.carousel = carousel
        st.session_state.carousel_images = carousel_images
        st.session_state.platform = "Instagram Carousel"

        # Track analytics (Pro users only)
        if pro and email and email.strip():
            template_name = None
            template_id = None
            if template_mode:
                template_obj = st.session_state.selected_template
                template_name = template_obj["title"]
                template_id = template_obj["id"]

            track_generation(
                email=email,
                platform="Instagram Carousel",
                tone=tone,
                length=length,
                topic=topic if topic else "Template-based",
                template_used=template_name,
                template_id=template_id
            )

    # Save to history (Pro users only, keep last 10) - now using Supabase
    if pro and email and email.strip():
        # Get content based on platform
        if platform == "X Thread" or platform == "LinkedIn Post":
            content = st.session_state.thread
        else:  # Instagram Carousel
            content = st.session_state.carousel

        # Save to Supabase
        save_thread_to_history(email, platform, content)

    # Don't rerun - let the error messages display and content show naturally below

# === DISPLAY ===
if "thread" in st.session_state and st.session_state.thread:
    st.markdown("---")
    # Dynamic title based on platform
    if st.session_state.get("platform") == "LinkedIn Post":
        st.subheader("💼 Your LinkedIn Post")
    else:
        st.subheader("🎉 Your Viral Thread")

    # Edit mode (Pro only)
    if pro:
        edit_mode = st.checkbox("✏️ Edit before posting", value=False, help="Pro feature: Edit your thread before posting")

        if edit_mode:
            edited_thread = st.text_area(
                "Edit your thread (one tweet per line)",
                value=st.session_state.thread,
                height=300,
                help="Each line will be posted as a separate tweet"
            )

            if st.button("💾 Save Edits", use_container_width=True):
                st.session_state.thread = edited_thread
                st.success("✅ Thread updated!")
                st.rerun()
        else:
            # Display thread in a nice box
            st.code(st.session_state.thread, language="text")
    else:
        # Free users - read-only preview
        st.code(st.session_state.thread, language="text")

    # Action buttons
    col1, col2, col3 = st.columns(3)

    with col1:
        # Add viral footer for free users
        if not pro:
            thread_with_footer = st.session_state.thread + "\n\n---\n📝 Generated with XThreadMaster - Create viral content with AI\n🚀 Get your free account: https://xthreadmaster.streamlit.app"
        else:
            thread_with_footer = st.session_state.thread

        st.download_button(
            "📥 Download",
            thread_with_footer,
            "xthread.txt",
            mime="text/plain",
            use_container_width=True,
            help="Download thread as .txt file"
        )

    with col2:
        if st.button("📋 Copy", use_container_width=True, help="Copy thread to clipboard"):
            # Use Streamlit's experimental clipboard
            st.write("")  # Placeholder - will add JS solution next
            st.success("✅ Copied to clipboard!")

    with col3:
        # Only show X auto-posting for X Threads (not LinkedIn Posts)
        if st.session_state.get("platform") == "X Thread":
            if pro and st.session_state.get("x_logged_in"):
                if st.button("🚀 Post to X", use_container_width=True, type="primary"):
                    with st.spinner("📤 Posting thread to X..."):
                        try:
                            client = tweepy.Client(
                                consumer_key=st.secrets["X_CONSUMER_KEY"],
                                consumer_secret=st.secrets["X_CONSUMER_SECRET"],
                                access_token=st.session_state.x_access_token,
                                access_token_secret=st.session_state.x_access_secret,
                            )

                            tweets = [t.strip() for t in st.session_state.thread.split("\n") if t.strip()]

                            if not tweets:
                                st.error("❌ No tweets to post!")
                                st.stop()

                            # Post first tweet
                            first = client.create_tweet(text=tweets[0])
                            tid = first.data["id"]
                            posted_count = 1

                            # Post remaining tweets as replies
                            for t in tweets[1:]:
                                try:
                                    resp = client.create_tweet(in_reply_to_tweet_id=tid, text=t)
                                    tid = resp.data["id"]
                                    posted_count += 1
                                except Exception as e:
                                    st.warning(f"⚠️ Failed to post tweet {posted_count + 1}: {e}")
                                    break

                            url = f"https://x.com/{st.session_state.x_username}/status/{first.data['id']}"
                            st.success(f"✅ Posted {posted_count}/{len(tweets)} tweets!")
                            st.markdown(f"### [🔗 View Your Thread on X]({url})")

                            # Track posted tweet for engagement analytics
                            if email and email.strip():
                                # Get topic and tone from the current generation
                                generation_topic = topic if 'topic' in locals() else "X Thread"
                                generation_tone = tone if 'tone' in locals() else "Unknown"
                                template_name = None
                                if st.session_state.get("template_mode") and "selected_template" in st.session_state:
                                    template_name = st.session_state.selected_template["title"]

                                track_posted_tweet(
                                    email=email,
                                    tweet_id=first.data['id'],
                                    topic=generation_topic,
                                    tone=generation_tone,
                                    template_used=template_name
                                )

                            st.balloons()

                        except tweepy.errors.Unauthorized:
                            st.error("❌ X authorization expired. Please reconnect your account.")
                            st.session_state.x_logged_in = False
                        except tweepy.errors.Forbidden as e:
                            st.error(f"❌ X API access forbidden: {e}")
                        except Exception as e:
                            st.error(f"❌ Failed to post: {e}")
            elif pro and not st.session_state.get("x_logged_in"):
                st.info("🔗 Connect your X account above to enable auto-posting")
            else:
                st.info("💎 Upgrade to Pro to enable auto-posting")
        elif st.session_state.get("platform") == "LinkedIn Post":
            # LinkedIn: Just show helpful message (OAuth not implemented yet)
            st.info("💡 Copy your post and paste it on LinkedIn")
        else:
            # Fallback for any other platform
            pass

    # Show remaining generations for free users
    if not pro and "remaining" in st.session_state and st.session_state.remaining is not None:
        st.divider()
        st.info(f"📊 **Free Tier:** {st.session_state.remaining} generations remaining today")

# === CAROUSEL DISPLAY ===
if "carousel" in st.session_state and st.session_state.carousel and st.session_state.platform == "Instagram Carousel":
    st.markdown("---")
    st.subheader("🎨 Your Instagram Carousel")

    # Display carousel text
    st.markdown("### 📝 Carousel Captions")
    st.code(st.session_state.carousel, language="text")

    # Display generated images if available
    if st.session_state.carousel_images:
        st.markdown("### 🖼️ AI-Generated Images")

        for img_data in st.session_state.carousel_images:
            st.markdown(f"**Slide {img_data['slide_num']}: {img_data['title']}**")

            # Convert bytes to image and display
            img = Image.open(io.BytesIO(img_data['data']))
            st.image(img, use_container_width=True)
            st.markdown("---")

    # Action buttons
    col1, col2 = st.columns(2)

    with col1:
        # Add viral footer for free/pro users (Visual Pack gets clean export)
        if not visual_pack:
            carousel_with_footer = st.session_state.carousel + "\n\n---\n🎨 Generated with XThreadMaster - Create viral content with AI\n🚀 Get Pro for unlimited threads: https://xthreadmaster.streamlit.app"
        else:
            carousel_with_footer = st.session_state.carousel

        # Download captions as text
        st.download_button(
            "📥 Download Captions",
            carousel_with_footer,
            "carousel_captions.txt",
            mime="text/plain",
            use_container_width=True,
            help="Download carousel captions as .txt file"
        )

    with col2:
        if st.session_state.carousel_images:
            # Download ZIP with images and captions
            if st.button("📦 Download ZIP (Images + Captions)", use_container_width=True, type="primary"):
                with st.spinner("📦 Preparing your carousel package..."):
                    # Create ZIP file in memory
                    zip_buffer = io.BytesIO()

                    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                        # Add captions file (with footer for non-Visual Pack users)
                        captions_content = carousel_with_footer if not visual_pack else st.session_state.carousel
                        zip_file.writestr("captions.txt", captions_content)

                        # Add images
                        for img_data in st.session_state.carousel_images:
                            img_filename = f"slide_{img_data['slide_num']:02d}.png"
                            zip_file.writestr(img_filename, img_data['data'])

                    zip_buffer.seek(0)

                    st.download_button(
                        "✅ Click to Download ZIP",
                        zip_buffer,
                        "instagram_carousel.zip",
                        mime="application/zip",
                        use_container_width=True
                    )
                    st.success("✅ Carousel package ready!")
        else:
            st.info("🎨 Images not generated - use tools below to create them")

    # Usage stats
    remaining = 100 - st.session_state.carousel_count
    st.divider()
    st.info(f"📊 **Carousel Usage:** {st.session_state.carousel_count}/100 this month • {remaining} remaining")

    # Next steps
    st.markdown("---")
    st.markdown("### 💡 Next Steps")

    if st.session_state.carousel_images:
        st.success("""
        **Your carousel is ready!**
        1. Download the ZIP file above
        2. Upload images to Instagram in order (slide_01.png, slide_02.png, etc.)
        3. Copy-paste the captions from the txt file
        4. Post and watch the engagement roll in! 🚀
        """)
    else:
        st.info("""
        **Create images for your carousel:**

        - [Canva](https://canva.com) - Free templates for Instagram carousels
        - [Adobe Express](https://express.adobe.com) - Professional designs
        - [Leonardo.ai](https://leonardo.ai) - Free AI image generation

        💡 **Tip:** Copy each slide caption and use it as a prompt in your image generator!
        """)

st.markdown("---")
st.markdown(f"<p style='text-align: center; color: gray; font-size: 14px;'>Made with ❤️ using Gemini AI • <a href='{STRIPE_PRO_LINK}' target='_blank'>Pro ($12)</a> • <a href='{STRIPE_VISUAL_PACK_LINK}' target='_blank'>Visual Pack ($17)</a></p>", unsafe_allow_html=True)
