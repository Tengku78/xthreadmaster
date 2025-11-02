import streamlit as st
import google.generativeai as genai
import requests
import tweepy
import streamlit.components.v1 as components  # <-- Added import
from datetime import date

# === CONFIG ===
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

# === SAFE MODEL SELECTION (Dynamic based on available models) ===
@st.cache_resource
def get_model():
    try:
        # List available models dynamically
        available_models = [m.name.split('/')[-1] for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        st.info(f"Available models detected: {available_models[:5]}...")  # Debug info
    except Exception as e:
        st.error(f"Failed to list models: {e}")
        st.stop()

    # Try common 2025 models in order of preference
    models_to_try = [
        'gemini-2.0-flash-exp',  # Experimental, as in your original
        'gemini-2.5-flash',      # Standard fast model
        'gemini-2.5-pro',        # Powerful model
        'gemini-1.5-pro',        # Legacy fallback if needed
    ]
    
    for model_name in models_to_try:
        if model_name in available_models:
            try:
                model = genai.GenerativeModel(model_name)
                # Quick silent test
                test_response = model.generate_content("test")
                if test_response and test_response.text:
                    st.success(f"Using {model_name}")
                    return model
            except Exception:
                continue
    
    # If none work, pick the first available that supports generateContent
    for model_name in available_models:
        try:
            model = genai.GenerativeModel(model_name)
            test_response = model.generate_content("test")
            if test_response and test_response.text:
                st.success(f"Using available model: {model_name}")
                return model
        except Exception:
            continue
    
    st.error("No supported Gemini model found. Check your API key, project, and billing in Google AI Studio.")
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
if "gen_count" not in st.session_state:
    st.session_state.gen_count = 0
    st.session_state.last_reset = date.today()

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
    except Exception:
        return False

pro = is_pro_user(email)

# === X OAUTH LOGIN ===
def handle_x_oauth():
    # === CALLBACK: After X redirect ===
    query_params = st.query_params.to_dict()
    if "oauth_verifier" in query_params:
        verifier = query_params["oauth_verifier"] if isinstance(query_params["oauth_verifier"], str) else query_params["oauth_verifier"][0]
        
        # Check for request tokens in session_state (set during login)
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

                # Cleanup temp tokens
                for k in ["oauth_token", "oauth_token_secret"]:
                    st.session_state.pop(k, None)
                # Clear query params to clean URL
                st.query_params.clear()
                st.rerun()
            except Exception as e:
                st.error(f"OAuth callback failed: {e}")
                st.info("This usually means the authorization timed out or tokens expired. Click 'Connect Your X Account' to start over.")
        else:
            st.error("Missing authorization tokens. Session expired—try logging in again.")
            st.info("This can happen if you take too long between steps. Start the login process fresh.")

    # === LOGIN BUTTON ===
    elif not st.session_state.get("x_logged_in", False):
        if st.button("Connect Your X Account (Pro Feature)", use_container_width=True):
            try:
                auth = tweepy.OAuth1UserHandler(
                    st.secrets["X_CONSUMER_KEY"],
                    st.secrets["X_CONSUMER_SECRET"],
                    callback="https://xthreadmaster.streamlit.app"
                )
                auth_url = auth.get_authorization_url(signin_with_twitter=True)
                st.session_state.oauth_token = auth.request_token['oauth_token']
                st.session_state.oauth_token_secret = auth.request_token['oauth_token_secret']
                
                # Show persistent login instructions
                st.info("Click the button below to authorize your X account. You'll be redirected back here after.")
                components.html(
                    f'''
                    <div style="text-align: center; margin: 20px 0;">
                        <a href="{auth_url}" target="_self">
                            <button style="
                                width: 100%;
                                padding: 14px;
                                background: #1DA1F2;
                                color: white;
                                border: none;
                                border-radius: 12px;
                                font-size: 18px;
                                font-weight: bold;
                                cursor: pointer;
                                box-shadow: 0 4px 8px rgba(0,0,0,0.1);
                            ">
                                Authorize with X
                            </button>
                        </a>
                    </div>
                    ''',
                    height=100
                )
                
                st.info("**Tip:** Complete the authorization in under 2 minutes to avoid session timeout.")
            except Exception as e:
                st.error(f"Login setup failed: {e}")
                st.info("Check your X API keys in secrets.toml and ensure callback URL is set to: https://xthreadmaster.streamlit.app")

    # === LOGGED IN ===
    else:
        col1, col2 = st.columns(2)
        with col1:
            st.success(f"Connected as @{st.session_state.x_username}")
        with col2:
            if st.button("Disconnect", use_container_width=True):
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
                st.markdown("**[Buy Now](https://buy.stripe.com/bJe5kEb5R8rm8Gc9pJ)**")
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
            if not thread:
                raise ValueError("Empty response from model")
        except Exception as e:
            st.error(f"Generation failed: {e}. Try a different topic or check your API key.")
            st.stop()

    st.session_state.thread = thread
    st.session_state.remaining = remaining
    st.rerun()

# === DISPLAY THREAD ===
if "thread" in st.session_state:
    thread = st.session_state.thread

    # Display with st.code for monospace + line breaks
    st.code(thread, language="text")

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
                    tweets = [t.strip() for t in thread.split("\n") if t.strip()]
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
            st.markdown("**[Buy Now](https://buy.stripe.com/bJe5kEb5R8rm8Gc9pJ)**")

# === FOOTER ===
st.markdown("---")
st.caption("**Built with Grok & Streamlit** | First $100 MRR = beer on me.")
