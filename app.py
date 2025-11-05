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
        st.info(f"Available models: {', '.join(models[:5])}")
    except Exception as e:
        st.warning(f"Could not list models: {e}")

    for name in ("gemini-2.0-flash-exp", "gemini-2.5-flash", "gemini-2.5-pro"):
        try:
            m = genai.GenerativeModel(name)
            test_response = m.generate_content("hi")
            if test_response and test_response.text:
                st.success(f"✅ Using {name}")
                return m
        except Exception as e:
            st.warning(f"Could not load {name}: {e}")
            continue

    st.error("❌ No model available. Please check your GEMINI_API_KEY in Streamlit secrets.")
    st.stop()

model = get_model()

st.set_page_config(page_title="XThreadMaster", page_icon="🚀", layout="centered")

# === INITIALIZE SESSION STATE ===
if "gen_count" not in st.session_state:
    st.session_state.gen_count = 0
if "last_reset" not in st.session_state:
    st.session_state.last_reset = date.today()
if "x_logged_in" not in st.session_state:
    st.session_state.x_logged_in = False
if "thread" not in st.session_state:
    st.session_state.thread = None

st.title("XThreadMaster – Viral X Threads in 10s")
st.markdown("**Generate, download, or auto-post viral X threads with AI.**")

# === INPUTS ===
email = st.text_input("Email (for Pro features)", placeholder="you@email.com", help="Enter your email to check Pro subscription status")
col1, col2 = st.columns(2)
with col1: topic = st.text_input("Topic", placeholder="AI side-hustles")
with col2: tone = st.selectbox("Tone", ["Casual", "Funny", "Pro", "Degen"])
length = st.slider("Length", 5, 15, 8)

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

# Show Pro status
if email and email.strip():
    if pro:
        st.success("✅ Pro account active - Unlimited generations & auto-posting enabled!")
    else:
        st.info("🆓 Free tier - 3 generations per day. [Upgrade to Pro](https://buy.stripe.com/...) for unlimited access!")

# === OAUTH: STATE PARAMETER (NO SESSION LOSS) ===
query = st.query_params

# CALLBACK - Handle OAuth return
if "oauth_verifier" in query and "oauth_token" in query:
    if not st.session_state.get("processing_oauth"):
        st.session_state.processing_oauth = True

        verifier = query["oauth_verifier"]
        oauth_token = query["oauth_token"]

        # CRITICAL: Get state parameter which contains the token secret
        req_secret = None
        if "state" in query:
            try:
                state_data = json.loads(urllib.parse.unquote(query["state"]))
                req_secret = state_data.get("secret")
                st.info(f"🔍 Debug: Retrieved secret from state parameter")
            except Exception as e:
                st.error(f"❌ Failed to parse state: {e}")

        # Fallback: try session state (usually won't work after redirect)
        if not req_secret and "oauth_token_secret" in st.session_state:
            req_secret = st.session_state.oauth_token_secret
            st.info(f"🔍 Debug: Retrieved secret from session state")

        if not req_secret:
            st.error("❌ OAuth session lost. The state parameter was not preserved during redirect.")
            st.warning("📝 Debug info: This happens when X redirects back without the state parameter.")
            st.info("💡 Try clicking the 'Connect X Account' button again and make sure you complete the authorization on X.")

            # Show what we received
            st.code(f"Received params: {dict(query)}")

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
            st.session_state.x_logged_in = True

            client = tweepy.Client(
                consumer_key=st.secrets["X_CONSUMER_KEY"],
                consumer_secret=st.secrets["X_CONSUMER_SECRET"],
                access_token=access[0],
                access_token_secret=access[1]
            )
            user = client.get_me(user_auth=False).data
            st.session_state.x_username = user.username

            # Clean up temporary state
            st.session_state.pop("oauth_token_secret", None)
            st.session_state.pop("processing_oauth", None)

            # Clear query params and rerun
            st.query_params.clear()
            st.success(f"✅ Connected as @{user.username}")
            st.rerun()
        except Exception as e:
            st.error(f"❌ OAuth failed: {e}")
            st.code(f"Error details: {str(e)}")
            st.session_state.processing_oauth = False
            st.query_params.clear()

# LOGIN BUTTON
if not st.session_state.get("x_logged_in"):
    st.info("🔗 Connect your X account to enable auto-posting (Pro feature)")

    if st.button("🚀 Connect X Account (Pro)", use_container_width=True):
        auth = tweepy.OAuth1UserHandler(
            st.secrets["X_CONSUMER_KEY"],
            st.secrets["X_CONSUMER_SECRET"],
            callback="https://xthreadmaster.streamlit.app"
        )
        try:
            auth_url = auth.get_authorization_url(signin_with_twitter=True)
            rt = auth.request_token

            # Store token secret in session state as backup
            st.session_state.oauth_token_secret = rt["oauth_token_secret"]

            # Also encode in state parameter for double redundancy
            state = urllib.parse.quote(json.dumps({
                "token": rt["oauth_token"],
                "secret": rt["oauth_token_secret"]
            }))
            final_url = f"{auth_url}&state={state}"

            st.markdown(f"### [👉 Click here to authorize with X]({final_url})")
            st.warning("⚠️ You will be redirected to X. After authorizing, you'll return here automatically.")
            st.info("💡 **Important:** Make sure cookies are enabled in your browser for this to work!")
        except Exception as e:
            st.error(f"❌ Setup failed: {e}")

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
if "thread" in st.session_state and st.session_state.thread:
    st.code(st.session_state.thread, language="text")
    st.download_button("📥 Download .txt", st.session_state.thread, "thread.txt", mime="text/plain")

    if pro and st.session_state.get("x_logged_in"):
        if st.button("🚀 Auto-Post to X", use_container_width=True, type="primary"):
            with st.spinner("Posting thread to X..."):
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
                    st.success(f"✅ Posted {posted_count}/{len(tweets)} tweets! [View Thread]({url})")
                    st.balloons()

                except tweepy.errors.Unauthorized:
                    st.error("❌ X authorization expired. Please reconnect your account.")
                    st.session_state.x_logged_in = False
                except tweepy.errors.Forbidden as e:
                    st.error(f"❌ X API access forbidden: {e}")
                except Exception as e:
                    st.error(f"❌ Failed to post: {e}")

    # Show remaining generations for free users
    if not pro and "remaining" in st.session_state and st.session_state.remaining is not None:
        st.info(f"📊 Free tier: {st.session_state.remaining} generations remaining today")

st.markdown("---")
st.caption("**Grok + Streamlit**")
