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

# === CONFIG ===
# NOTE: genai.configure() is now called lazily in get_model() to prevent deployment hangs

# Get Stripe payment links from secrets (with fallback)
STRIPE_PRO_LINK = st.secrets.get("STRIPE_PRO_LINK", "#")
STRIPE_VISUAL_PACK_LINK = st.secrets.get("STRIPE_VISUAL_PACK_LINK", "#")

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
with st.sidebar:
    st.title("ℹ️ About")
    st.markdown("""
    **XThreadMaster** generates viral content for X & Instagram using AI.

    ### ✨ Features
    - 🤖 AI-powered content generation
    - 🎨 Multiple tone options
    - 📥 Download content
    - 🚀 Auto-post to X (Pro+)

    ### 🆓 Free Tier
    - 3 X threads per day
    - Manual posting

    ### 💎 Pro ($12/mo)
    - ♾️ Unlimited X threads
    - 🚀 One-click auto-posting to X
    - 🔗 X account integration
    - ✏️ Edit before posting
    - 📚 Thread history (last 10)

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
if "thread" not in st.session_state:
    st.session_state.thread = None
if "carousel" not in st.session_state:
    st.session_state.carousel = None
if "carousel_images" not in st.session_state:
    st.session_state.carousel_images = []
if "platform" not in st.session_state:
    st.session_state.platform = "X Thread"
if "thread_history" not in st.session_state:
    st.session_state.thread_history = []

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

# === CONTENT SETTINGS ===
st.subheader("📝 Content Settings")

# Platform selector
platform_options = ["X Thread"]
if visual_pack:
    platform_options.append("Instagram Carousel")

platform = st.selectbox(
    "Platform*",
    platform_options,
    help="Choose which platform to generate content for"
)

col1, col2 = st.columns(2)
with col1:
    topic = st.text_input("Topic*", placeholder="AI side-hustles, productivity tips, etc.", help="What should your content be about?")
with col2:
    tone = st.selectbox("Tone", ["Casual", "Funny", "Pro", "Degen"], help="Choose the writing style")

# Dynamic length slider based on platform
if platform == "X Thread":
    length = st.slider("Thread Length (tweets)", 5, 15, 8, help="Number of tweets in your thread")
else:  # Instagram Carousel
    length = st.slider("Carousel Length (slides)", 5, 10, 7, help="Number of slides in your carousel")

# Update sidebar with thread history (Pro only)
if pro:
    with st.sidebar:
        st.markdown("---")
        st.subheader("📚 Thread History")

        if st.session_state.thread_history:
            st.caption("Your last 10 threads")
            for idx, entry in enumerate(st.session_state.thread_history):
                with st.expander(f"🧵 {entry['topic'][:30]}...", expanded=False):
                    st.caption(f"**Tone:** {entry['tone']} | **Length:** {entry['length']} tweets")
                    st.caption(f"**Created:** {datetime.fromisoformat(entry['timestamp']).strftime('%b %d, %I:%M %p')}")

                    if st.button(f"📥 Load", key=f"load_{idx}", use_container_width=True):
                        st.session_state.thread = entry['thread']
                        st.rerun()
        else:
            st.caption("Generate threads to see them here!")

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
button_text = "✨ Generate Viral Thread" if platform == "X Thread" else "🎨 Generate Instagram Carousel"

if st.button(button_text, type="primary", use_container_width=True):
    if not topic.strip():
        st.warning("⚠️ Please enter a topic")
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

    else:  # Instagram Carousel
        # Check carousel monthly limit (100/month soft cap)
        if st.session_state.carousel_count >= 100:
            st.error("🚫 Monthly carousel limit reached: 100 carousels per month")
            st.info("You've hit the soft cap for this month. This limit resets on the 1st of next month.")
            st.warning("💡 Need more? Contact support for enterprise pricing.")
            st.stop()

        # Generate Instagram Carousel
        with st.spinner("🎨 Generating your Instagram carousel..."):
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

    # Save to history (Pro users only, keep last 10)
    if pro:
        history_entry = {
            "topic": topic,
            "tone": tone,
            "length": length,
            "content": thread if platform == "X Thread" else carousel,
            "platform": platform,
            "timestamp": datetime.now().isoformat()
        }
        st.session_state.thread_history.insert(0, history_entry)
        st.session_state.thread_history = st.session_state.thread_history[:10]

    # Don't rerun - let the error messages display and content show naturally below

# === DISPLAY ===
if "thread" in st.session_state and st.session_state.thread:
    st.markdown("---")
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
        st.download_button(
            "📥 Download",
            st.session_state.thread,
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
        # Download captions as text
        st.download_button(
            "📥 Download Captions",
            st.session_state.carousel,
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
                        # Add captions file
                        zip_file.writestr("captions.txt", st.session_state.carousel)

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
st.caption(f"Made with ❤️ using Gemini AI • [Pro ($12)]({STRIPE_PRO_LINK}) • [Visual Pack ($17)]({STRIPE_VISUAL_PACK_LINK})")
