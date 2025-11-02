import streamlit as st
import google.generativeai as genai
import requests
import tweepy
import urllib.parse
import json
from datetime import date

# === CONFIG ===
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

# === MODEL ===
@st.cache_resource
def get_model():
    try:
        models = [m.name.split("/")[-1] for m in genai.list_models() if "generateContent" in m.supported_generation_methods]
        st.info(f"Models: {models[:5]}")
    except: pass
    for name in ("gemini-2.0-flash-exp", "gemini-2.5-flash", "gemini-2.5-pro"):
        try:
            m = genai.GenerativeModel(name)
            if m.generate_content("hi").text:
                st.success(f"Using {name}")
                return m
        except: pass
    st.error("No model. Check API key.")
    st.stop()

model = get_model()

st.set_page_config(page_title="XThreadMaster", page_icon="rocket", layout="centered")
st.title("XThreadMaster – Viral X Threads in 10s")
st.markdown("**Generate, download, or auto-post.**")

# === INPUTS ===
email = st.text_input("Email (Pro)", placeholder="you@email.com")
col1, col2 = st.columns(2)
with col1: topic = st.text_input("Topic", placeholder="AI side-hustles")
with col2: tone = st.selectbox("Tone", ["Casual", "Funny", "Pro", "Degen"])
length = st.slider("Length", 5, 15, 8)

# === LIMIT ===
if "gen_count" not in st.session_state:
    st.session_state.gen_count = 0
    st.session_state.last_reset = date.today()
if st.session_state.last_reset != date.today():
    st.session_state.gen_count = 0
    st.session_state.last_reset = date.today()

# === PRO ===
def is_pro(e):
    if not e: return False
    try:
        custs = requests.get("https://api.stripe.com/v1/customers", params={"email": e}, auth=(st.secrets["STRIPE_SECRET_KEY"], "")).json().get("data", [])
        for c in custs:
            subs = requests.get(f"https://api.stripe.com/v1/subscriptions", params={"customer": c["id"], "status": "active"}, auth=(st.secrets["STRIPE_SECRET_KEY"], "")).json().get("data", [])
            if subs: return True
    except: pass
    return False
pro = is_pro(email)

# === OAUTH: STATE PARAMETER (NO SESSION LOSS) ===
query = st.query_params

# CALLBACK
if "oauth_verifier" in query and "state" in query:
    verifier = query["oauth_verifier"]
    state = urllib.parse.unquote(query["state"])
    try:
        tokens = json.loads(state)
        req_token = tokens["token"]
        req_secret = tokens["secret"]
    except:
        st.error("Invalid state. Try again.")
        st.stop()

    auth = tweepy.OAuth1UserHandler(
        st.secrets["X_CONSUMER_KEY"],
        st.secrets["X_CONSUMER_SECRET"],
        callback="https://xthreadmaster.streamlit.app"
    )
    auth.request_token = {"oauth_token": req_token, "oauth_token_secret": req_secret}
    try:
        access = auth.get_access_token(verifier)
        st.session_state.x_access_token = access[0]
        st.session_state.x_access_secret = access[1]
        st.session_state.x_logged_in = True
        client = tweepy.Client(
            consumer_key=st.secrets["X_CONSUMER_KEY"],
            consumer_secret=st.secrets["X_CONSUMER_SECRET"],
            access_token=access[0],
            access_token_secret=access[1]
        )
        user = client.get_me(user_auth=False).data
        st.session_state.x_username = user.username
        st.success(f"Connected as @{user.username}")
        st.query_params.clear()
        st.rerun()
    except Exception as e:
        st.error(f"OAuth failed: {e}")

# LOGIN BUTTON
elif not st.session_state.get("x_logged_in"):
    if st.button("Connect X Account (Pro)", use_container_width=True):
        auth = tweepy.OAuth1UserHandler(
            st.secrets["X_CONSUMER_KEY"],
            st.secrets["X_CONSUMER_SECRET"],
            callback="https://xthreadmaster.streamlit.app"
        )
        try:
            auth_url = auth.get_authorization_url(signin_with_twitter=True)
            rt = auth.request_token
            state = urllib.parse.quote(json.dumps({
                "token": rt["oauth_token"],
                "secret": rt["oauth_token_secret"]
            }))
            final_url = f"{auth_url}&state={state}"
            st.markdown(f"[**Authorize with X (new tab)**]({final_url})")
            st.info("Approve → return here. Works every time.")
        except Exception as e:
            st.error(f"Setup failed: {e}")

# LOGGED IN
else:
    col1, col2 = st.columns(2)
    with col1: st.success(f"@{st.session_state.x_username}")
    with col2:
        if st.button("Disconnect", use_container_width=True):
            for k in ["x_access_token", "x_access_secret", "x_username", "x_logged_in"]:
                st.session_state.pop(k, None)
            st.rerun()

# === GENERATE ===
if st.button("GENERATE VIRAL THREAD", type="primary", use_container_width=True):
    if not topic.strip():
        st.warning("Enter topic!")
        st.stop()

    if not pro and st.session_state.gen_count >= 3:
        st.error("Free limit: 3/day.")
        with st.expander("Pro"): st.markdown("**[Buy](https://buy.stripe.com/...)***")
        st.stop()

    if not pro: st.session_state.gen_count += 1
    remaining = 3 - st.session_state.gen_count if not pro else None

    with st.spinner("Generating..."):
        prompt = f"VIRAL X thread: \"{topic}\"\n- {length} tweets\n- Tone: {tone}\n- Hook → Value → CTA\n- Emojis\n- <100 chars\n- ONE PER LINE"
        try:
            thread = model.generate_content(prompt).text.strip()
        except Exception as e:
            st.error(f"AI error: {e}")
            st.stop()

    st.session_state.thread = thread
    st.session_state.remaining = remaining
    st.rerun()

# === DISPLAY ===
if "thread" in st.session_state:
    st.code(st.session_state.thread, language="text")
    st.download_button("Download .txt", st.session_state.thread, "thread.txt")

    if pro and st.session_state.get("x_logged_in"):
        if st.button("Auto-Post", use_container_width=True):
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
                st.success(f"Posted! [View]({url})")
                st.balloons()

    status = f"Ready! ({remaining} left)" if not pro else "Pro"
    st.success(status)

st.markdown("---")
st.caption("**Grok + Streamlit**")
