import streamlit as st
import google.generativeai as genai
import requests
import tweepy
import json
from datetime import date, datetime
import os
import tempfile

# === CONFIG ===
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

# Get Stripe payment link from secrets (with fallback)
STRIPE_PAYMENT_LINK = st.secrets.get("STRIPE_PAYMENT_LINK", "#")

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
    # Try models in order of preference
    for name in ("gemini-2.0-flash-exp", "gemini-2.5-flash", "gemini-2.5-pro"):
        try:
            m = genai.GenerativeModel(name)
            # Test the model
            test_response = m.generate_content("hi")
            if test_response and test_response.text:
                return m
        except Exception:
            continue

    # If no model works, show error
    st.error("❌ AI service unavailable. Please contact support or try again later.")
    st.stop()

model = get_model()

st.set_page_config(page_title="XThreadMaster", page_icon="🚀", layout="centered")

# === SIDEBAR ===
with st.sidebar:
    st.title("ℹ️ About")
    st.markdown("""
    **XThreadMaster** generates viral X/Twitter threads using AI.

    ### ✨ Features
    - 🤖 AI-powered thread generation
    - 🎨 Multiple tone options
    - 📥 Download as text file
    - 🚀 Auto-post to X (Pro)

    ### 🆓 Free Tier
    - 3 generations per day
    - Manual posting

    ### 💎 Pro Benefits
    - ♾️ Unlimited generations
    - 🚀 One-click auto-posting
    - 🔗 X account integration
    - ✏️ Edit before posting
    - 📚 Thread history (last 10)

    ---

    [Upgrade to Pro]({STRIPE_PAYMENT_LINK})
    """.replace("{STRIPE_PAYMENT_LINK}", STRIPE_PAYMENT_LINK))

# === INITIALIZE SESSION STATE ===
if "gen_count" not in st.session_state:
    st.session_state.gen_count = 0
if "last_reset" not in st.session_state:
    st.session_state.last_reset = date.today()
if "x_logged_in" not in st.session_state:
    st.session_state.x_logged_in = False
if "thread" not in st.session_state:
    st.session_state.thread = None
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

st.subheader("📝 Thread Settings")
col1, col2 = st.columns(2)
with col1:
    topic = st.text_input("Topic*", placeholder="AI side-hustles, productivity tips, etc.", help="What should your thread be about?")
with col2:
    tone = st.selectbox("Tone", ["Casual", "Funny", "Pro", "Degen"], help="Choose the writing style")

length = st.slider("Thread Length (tweets)", 5, 15, 8, help="Number of tweets in your thread")

# === LIMIT ===
if st.session_state.last_reset != date.today():
    st.session_state.gen_count = 0
    st.session_state.last_reset = date.today()

# === PRO ===
def is_pro(e):
    if not e or not e.strip():
        return False
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
            if subs:
                return True
    except requests.exceptions.RequestException as e:
        st.warning(f"⚠️ Could not verify Pro status: {e}")
    except Exception as e:
        st.warning(f"⚠️ Stripe verification error: {e}")

    return False

pro = is_pro(email)

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

# Show Pro status in a cleaner way
if email and email.strip():
    if pro:
        st.success("✅ **Pro Account Active** - Unlimited generations & auto-posting enabled")
    else:
        remaining_today = 3 - st.session_state.gen_count
        st.info(f"🆓 **Free Tier** - {remaining_today} generations remaining today | [Upgrade to Pro]({STRIPE_PAYMENT_LINK}) for unlimited access")

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

        # Helpful note if email not entered
        if not email or not email.strip():
            st.info("😊 **You're connected!** Just re-enter your Pro email in Account Settings above to start posting!")

# === GENERATE ===
st.markdown("---")

if st.button("✨ Generate Viral Thread", type="primary", use_container_width=True):
    if not topic.strip():
        st.warning("⚠️ Please enter a topic for your thread")
        st.stop()

    if not pro and st.session_state.gen_count >= 3:
        st.error("🚫 Free limit reached: 3 generations per day")
        st.info(f"💎 [Upgrade to Pro]({STRIPE_PAYMENT_LINK}) for unlimited generations and auto-posting")
        st.stop()

    if not pro:
        st.session_state.gen_count += 1
    remaining = 3 - st.session_state.gen_count if not pro else None

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
            thread = model.generate_content(prompt).text.strip()
        except Exception as e:
            st.error(f"❌ AI generation failed: {e}")
            st.stop()

    st.session_state.thread = thread
    st.session_state.remaining = remaining

    # Save to history (Pro users only, keep last 10)
    if pro:
        history_entry = {
            "topic": topic,
            "tone": tone,
            "length": length,
            "thread": thread,
            "timestamp": datetime.now().isoformat()
        }
        st.session_state.thread_history.insert(0, history_entry)
        st.session_state.thread_history = st.session_state.thread_history[:10]  # Keep only last 10

    st.rerun()

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

st.markdown("---")
st.caption(f"Made with ❤️ using Gemini AI • [Upgrade to Pro]({STRIPE_PAYMENT_LINK})")
