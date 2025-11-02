import streamlit as st
import google.generativeai as genai
import requests
import tweepy
from datetime import date

# -------------------------------------------------
# 1. Gemini model (dynamic, safe)
# -------------------------------------------------
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

@st.cache_resource
def get_model():
    try:
        avail = [m.name.split("/")[-1] for m in genai.list_models()
                if "generateContent" in m.supported_generation_methods]
        st.info(f"Detected models: {avail[:5]}")
    except Exception as e:
        st.error(f"Model list error: {e}")
        st.stop()

    for name in ("gemini-2.0-flash-exp", "gemini-2.5-flash", "gemini-2.5-pro"):
        if any(name in m for m in avail):
            try:
                m = genai.GenerativeModel(name)
                if m.generate_content("ping").text:
                    st.success(f"Using {name}")
                    return m
            except:
                continue
    st.error("No usable Gemini model – check API key / billing.")
    st.stop()

model = get_model()

# -------------------------------------------------
# 2. UI basics
# -------------------------------------------------
st.set_page_config(page_title="XThreadMaster", page_icon="rocket", layout="centered")
st.title("XThreadMaster – Viral X Threads in 10s")
st.markdown("**Generate, download, or auto-post.**")

email = st.text_input("Email (Pro unlock)", placeholder="you@email.com")
col1, col2 = st.columns(2)
with col1: topic = st.text_input("Topic/Niche", placeholder="AI side-hustles")
with col2: tone = st.selectbox("Tone", ["Casual", "Professional", "Funny", "Inspirational", "Degen"])
length = st.slider("Thread length", 5, 15, 8)

# -------------------------------------------------
# 3. Free-user daily limit (session_state)
# -------------------------------------------------
if "gen_count" not in st.session_state:
    st.session_state.gen_count = 0
    st.session_state.last_reset = date.today()
if st.session_state.last_reset != date.today():
    st.session_state.gen_count = 0
    st.session_state.last_reset = date.today()

# -------------------------------------------------
# 4. Pro check (Stripe)
# -------------------------------------------------
def is_pro(email):
    if not email: return False
    try:
        custs = requests.get(
            "https://api.stripe.com/v1/customers",
            params={"email": email},
            auth=(st.secrets["STRIPE_SECRET_KEY"], "")
        ).json().get("data", [])
        for c in custs:
            subs = requests.get(
                f"https://api.stripe.com/v1/subscriptions",
                params={"customer": c["id"], "status": "active"},
                auth=(st.secrets["STRIPE_SECRET_KEY"], "")
            ).json().get("data", [])
            if subs: return True
    except:
        pass
    return False

pro = is_pro(email)

# -------------------------------------------------
# 5. X OAuth – **the only part that changed**
# -------------------------------------------------
def handle_x_oauth():
    # ---------- CALLBACK ----------
    if "oauth_verifier" in st.query_params:
        verifier = st.query_params["oauth_verifier"]
        # request token was saved in session_state before redirect
        if "req_token" in st.session_state and "req_secret" in st.session_state:
            auth = tweepy.OAuth1UserHandler(
                st.secrets["X_CONSUMER_KEY"],
                st.secrets["X_CONSUMER_SECRET"],
                callback="https://xthreadmaster.streamlit.app"
            )
            auth.request_token = {
                "oauth_token": st.session_state.req_token,
                "oauth_token_secret": st.session_state.req_secret,
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
                    access_token_secret=access_secret,
                )
                me = client.get_me(user_auth=False).data
                st.session_state.x_username = me.username
                st.success(f"Connected as @{me.username}")
                # clean up
                for k in ("req_token", "req_secret"):
                    st.session_state.pop(k, None)
                st.query_params.clear()
                st.rerun()
            except Exception as e:
                st.error(f"OAuth error: {e}")
        else:
            st.error("Session lost – start login again.")
        return

    # ---------- NOT LOGGED IN ----------
    if not st.session_state.get("x_logged_in"):
        if st.button("Connect X Account (Pro)", use_container_width=True):
            auth = tweepy.OAuth1UserHandler(
                st.secrets["X_CONSUMER_KEY"],
                st.secrets["X_CONSUMER_SECRET"],
                callback="https://xthreadmaster.streamlit.app"
            )
            try:
                auth_url = auth.get_authorization_url(signin_with_twitter=True)
                # SAVE request token for the callback
                st.session_state.req_token = auth.request_token["oauth_token"]
                st.session_state.req_secret = auth.request_token["oauth_token_secret"]
                st.markdown(f"[**Authorize with X (opens new tab)**]({auth_url})")
                st.info("Approve quickly – you’ll be sent back here.")
            except Exception as e:
                st.error(f"Setup failed: {e}")
        return

    # ---------- LOGGED IN ----------
    col1, col2 = st.columns(2)
    with col1:
        st.success(f"@{st.session_state.x_username}")
    with col2:
        if st.button("Disconnect", use_container_width=True):
            for k in ("x_access_token", "x_access_secret", "x_username", "x_logged_in"):
                st.session_state.pop(k, None)
            st.rerun()

handle_x_oauth()

# -------------------------------------------------
# 6. Generate thread
# -------------------------------------------------
if st.button("GENERATE VIRAL THREAD", type="primary", use_container_width=True):
    if not topic.strip():
        st.warning("Enter a topic.")
        st.stop()

    # free-user limit
    if not pro and st.session_state.gen_count >= 3:
        st.error("Free limit: 3/day – upgrade to Pro.")
        with st.expander("Pro ($12/mo)"):
            st.markdown("**[Buy Now](https://buy.stripe.com/...)***")
        st.stop()

    if not pro:
        st.session_state.gen_count += 1
    remaining = 3 - st.session_state.gen_count if not pro else None

    with st.spinner("Generating..."):
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
            thread = model.generate_content(prompt).text.strip()
        except Exception as e:
            st.error(f"AI error: {e}")
            st.stop()

    st.session_state.thread = thread
    st.session_state.remaining = remaining
    st.rerun()

# -------------------------------------------------
# 7. Show result + post
# -------------------------------------------------
if "thread" in st.session_state:
    st.code(st.session_state.thread, language="text")
    st.download_button("Download .txt", st.session_state.thread, "xthread.txt", "text/plain")

    if pro and st.session_state.get("x_logged_in"):
        if st.button("Auto-Post to X", use_container_width=True):
            with st.spinner("Posting..."):
                client = tweepy.Client(
                    consumer_key=st.secrets["X_CONSUMER_KEY"],
                    consumer_secret=st.secrets["X_CONSUMER_SECRET"],
                    access_token=st.session_state.x_access_token,
                    access_token_secret=st.session_state.x_access_secret,
                )
                tweets = [t for t in st.session_state.thread.split("\n") if t.strip()]
                first = client.create_tweet(text=tweets[0])
                tid = first.data["id"]
                for t in tweets[1:]:
                    resp = client.create_tweet(in_reply_to_tweet_id=tid, text=t)
                    tid = resp.data["id"]
                url = f"https://x.com/{st.session_state.x_username}/status/{first.data['id']}"
                st.success(f"Posted! [View thread]({url})")
                st.balloons()

    status = f"Ready! ({remaining} free left)" if not pro else "Pro – unlimited"
    st.success(status)

    if not pro:
        with st.expander("Upgrade to Pro"):
            st.markdown("**[Buy Now](https://buy.stripe.com/...)***")

st.markdown("---")
st.caption("**Built with Grok & Streamlit**")
