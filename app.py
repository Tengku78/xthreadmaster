import streamlit as st
import google.generativeai as genai
import requests
import os
import tweepy
from datetime import date

# === CONFIG ===
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

# === SAFE MODEL SELECTION ===
@st.cache_resource
def get_model():
    try:
        model = genai.GenerativeModel('gemini-2.0-flash')
        model.generate_content("test")  # Quick access test
        st.toast("Using gemini-2.0-flash", icon="Success")
        return model
    except Exception as e:
        st.warning(f"gemini-2.0-flash not available: {e}")
        try:
            model = genai.GenerativeModel('gemini-1.5-flash')
            model.generate_content("test")
            st.toast("Fallback to gemini-1.5-flash", icon="Success")
            return model
        except Exception as e2:
            st.error("Gemini API Error")
            st.error("1. Check `GEMINI_API_KEY` in Secrets")
            st.error("2. Enable Generative AI API in Google Cloud")
            st.error("3. Enable billing")
            st.stop()

model = get_model()

st.set_page_config(page_title="XThreadMaster", page_icon="rocket", layout="centered")
st.title("XThreadMaster – Viral X Threads in 10s")
st.markdown("**Generate, download, or auto-post to your X account.**")

# === EMAIL INPUT ===
email = st.text_input("Enter your email (for Pro unlock)", placeholder="your@email.com")

# === INPUTS ===
col1, col2 = st.columns(2)
with col1:
    topic = st.text_input("Topic/Niche", placeholder="AI side hustles, fitness tips, etc.")
with col2:
    tone = st.selectbox("Tone", ["Casual", "Professional", "Funny", "Inspirational", "Degen"])

length = st.slider("Thread Length", 5, 15, 8, help="Number of tweets")

# === DAILY FREE LIMIT (session_state) ===
def init_daily_limit():
    if "gen_count" not in st.session_state:
        st.session_state.gen_count = 0
        st.session_state.last_reset = date.today()

init_daily_limit()
today = date.today()
if st.session_state.last_reset != today:
    st.session_state.gen_count = 0
    st.session_state.last_reset = today

# === PRO CHECK ===
def is_pro_user(email):
    if not email:
        return False
    try:
        response = requests.get(
            "https://api.stripe.com/v1/customers",
            params={"email": email},
            auth=(st.secrets["STRIPE_SECRET_KEY"], "")
        )
        customers = response.json().get("data", [])
        for cust in customers:
            subs = requests.get(
                f"https://api.stripe.com/v1/subscriptions",
                params={"customer": cust["id"], "status": "active"},
                auth=(st.secrets["STRIPE_SECRET_KEY"], "")
            ).json().get("data", [])
            if subs:
                return True
        return False
    except Exception as e:
        st.error(f"Pro check failed: {e}")
        return False

pro = is_pro_user(email)

# === X OAUTH LOGIN (URL-BASED, NO SESSION LOSS) ===
def handle_x_oauth():
    # === CALLBACK: After X redirect ===
    if "oauth_verifier" in st.query_params:
        verifier = st.query_params["oauth_verifier"]
        
        if "oauth_token" in st.session_state and "oauth_token_secret" in st.session_state:
            auth = tweepy.OAuth1UserHandler(
                st.secrets["X_CONSUMER_KEY"],
                st.secrets["X_CONSUMER_SECRET"],
                callback="https://xthreadmaster.streamlit.app"
            )
            auth.request_token = {
                'oauth_token': st.session_state.oauth_token,
                'oauth_token_secret': st.session_state.oauth_token_secret
            }
            try:
                access_token, access_secret = auth.get_access_token(verifier)
                st.session_state.x_access_token = access_token
                st.session_state.x_access_secret = access_secret
                st.session_state.x_logged_in = True

                client = tweepy.Client(
                    consumer_key=st.secrets["X_CONSUMER_KEY"],
                    consumer_secret=st.secrets["X_CONSUMER_SECRET"],
                    access_token=access_token,
                    access_token_secret=access_secret
                )
                user = client.get_me(user_auth=False)
                st.session_state.x_username = user.data.username
                st.success(f"Connected as @{user.data.username}!")

                # Cleanup
                for k in ["oauth_token", "oauth_token_secret"]:
                    if k in st.session_state:
                        del st.session_state[k]
                st.query_params.clear()
                st.rerun()
            except Exception as e:
                st.error(f"OAuth failed: {e}")
        else:
            st.error("Session expired. Try logging in again.")

    # === LOGIN BUTTON ===
    elif not st.session_state.get("x_logged_in", False):
        if st.button("Connect Your X Account (Pro Feature)"):
            auth = tweepy.OAuth1UserHandler(
                st.secrets["X_CONSUMER_KEY"],
                st.secrets["X_CONSUMER_SECRET"],
                callback="https://xthreadmaster.streamlit.app"
            )
            try:
                auth_url = auth.get_authorization_url()
                st.session_state.oauth_token = auth.request_token['oauth_token']
                st.session_state.oauth_token_secret = auth.request_token['oauth_token_secret']
                st.markdown(f"[Login to X]({auth_url})")
            except Exception as e:
                st.error(f"Login failed: {e}")

    # === LOGGED IN ===
    else:
        st.success(f"Connected as @{st.session_state.x_username}")
        if st.button("Disconnect"):
            keys = ["x_access_token", "x_access_secret", "x_username", "x_logged_in"]
            for k in keys:
                st.session_state.pop(k, None)
            st.success("Disconnected!")
            st.rerun()

# Run OAuth
handle_x_oauth()

# === GENERATE ===
if st.button("GENERATE VIRAL THREAD", type="primary", use_container_width=True):
    if not topic.strip():
        st.warning("Enter a topic first!")
        st.stop()

    # === FREE LIMIT CHECK ===
    if not pro:
        if st.session_state.gen_count >= 3:
            st.error("Free limit: 3/day. Upgrade to Pro for unlimited.")
            with st.expander("Upgrade to Pro ($12/mo)"):
                st.markdown("**[Buy Now](https://buy.stripe.com/bJe5kEb5R8rm8Gc9pJ28800)**")
            st.stop()
        st.session_state.gen_count += 1
        remaining = 3 - st.session_state.gen_count
    else:
        remaining = None

    # === GENERATE ===
    with st.spinner("Generating viral thread..."):
        prompt = f"""
        Write a VIRAL X thread about: "{topic}"
        - {length} tweets
        - Tone: {tone}
        - Tweet 1: Killer hook
        - Middle: 3-5 value bombs
        - Last: Strong CTA
        - Emojis EVERYWHERE
        - <100 chars/tweet
        - NO NUMBERING
        - ONE TWEET PER LINE
        OUTPUT ONLY THE THREAD.
        """
        try:
            response = model.generate_content(prompt)
            thread = response.text.strip()
        except Exception as e:
            st.error(f"Generation failed: {e}")
            st.stop()

    st.session_state.thread = thread
    st.session_state.remaining = remaining
    st.rerun()

# === DISPLAY THREAD ===
if "thread" in st.session_state:
    thread = st.session_state.thread

    st.markdown(
        f"""
        <div style="
            background-color: #1a1a1a;
            color: #ffffff;
            padding: 20px;
            border-radius: 16px;
            border: 1px solid #333;
            font-family: 'Courier New', monospace;
            font-size: 16px;
            line-height: 1.7;
            max-height: 600px;
            overflow-y: auto;
            white-space: pre-wrap;
            word-wrap: break-word;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        ">
        {thread.replace(chr(10), '<br>')}
        </div>
        """,
        unsafe_allow_html=True
    )

    st.download_button("Download .txt", thread, "xthread.txt", "text/plain")

    # === AUTO-POST (ONLY PRO + LOGGED IN) ===
    if pro and st.session_state.get("x_logged_in"):
        if st.button("Auto-Post to Your X Account", key="post_x", use_container_width=True):
            with st.spinner("Posting thread..."):
                try:
                    client = tweepy.Client(
                        consumer_key=st.secrets["X_CONSUMER_KEY"],
                        consumer_secret=st.secrets["X_CONSUMER_SECRET"],
                        access_token=st.session_state.x_access_token,
                        access_token_secret=st.session_state.x_access_secret
                    )
                    tweets = [t for t in thread.split("\n") if t.strip()]
                    if not tweets:
                        st.error("No tweets to post.")
                        st.stop()

                    first = client.create_tweet(text=tweets[0])
                    tweet_id = first.data['id']
                    for t in tweets[1:]:
                        resp = client.create_tweet(in_reply_to_tweet_id=tweet_id, text=t)
                        tweet_id = resp.data['id']

                    url = f"https://x.com/{st.session_state.x_username}/status/{first.data['id']}"
                    st.success(f"Posted! [View Thread]({url})")
                    st.balloons()
                except Exception as e:
                    st.error(f"Post failed: {e}")

    # === STATUS ===
    if not pro:
        st.success(f"Thread ready! ({st.session_state.remaining} free left today)")
    else:
        st.success("Pro Thread Ready – Unlimited!")

    # === UPSELL ===
    if not pro:
        with st.expander("Upgrade to Pro ($12/mo)"):
            st.markdown("**[Buy Now](https://buy.stripe.com/bJe5kEb5R8rm8Gc9pJ28800)**")

# === FOOTER ===
st.markdown("---")
st.caption("**Built with Grok & Streamlit** | First $100 MRR = beer on me.")
