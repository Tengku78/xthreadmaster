import streamlit as st
import google.generativeai as genai
import requests
import os
import tweepy

# === CONFIG ===
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
model = genai.GenerativeModel('gemini-1.5-flash')  # Assuming 'gemini-2.0-flash' may not exist; adjust if needed

st.set_page_config(page_title="XThreadMaster", page_icon="🚀", layout="centered")
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
    except:
        return False

pro = is_pro_user(email)

# === X OAUTH LOGIN (URL-BASED, NO SESSION LOSS) ===
def handle_x_oauth():
    # Step 3: Callback — Capture verifier from URL
    query_params = st.query_params.to_dict()
    if "oauth_verifier" in query_params:
        verifier = query_params["oauth_verifier"][0]
        oauth_token = query_params.get("oauth_token", [""])[0]
        
        if "request_token" in st.session_state and "request_token_secret" in st.session_state:
            request_token = st.session_state.request_token
            request_token_secret = st.session_state.request_token_secret
            
            auth = tweepy.OAuth1UserHandler(
                st.secrets["X_CONSUMER_KEY"],
                st.secrets["X_CONSUMER_SECRET"]
            )
            auth.request_token = {
                "oauth_token": request_token,
                "oauth_token_secret": request_token_secret
            }
            try:
                access_token, access_token_secret = auth.get_access_token(verifier)
                st.session_state.x_access_token = access_token
                st.session_state.x_access_secret = access_token_secret
                st.session_state.x_logged_in = True
                
                client = tweepy.Client(
                    consumer_key=st.secrets["X_CONSUMER_KEY"],
                    consumer_secret=st.secrets["X_CONSUMER_SECRET"],
                    access_token=st.session_state.x_access_token,
                    access_token_secret=st.session_state.x_access_secret
                )
                user = client.get_me()
                st.session_state.x_username = user.data.username
                st.success(f"Connected as @{st.session_state.x_username}!")
                
                # Clean up
                del st.session_state.request_token
                del st.session_state.request_token_secret
                
                # Clean URL
                st.query_params.clear()
            except Exception as e:
                st.error(f"OAuth failed: {e}")
        else:
            st.error("Missing request token. Try again.")

    # Step 1: Show login button
    elif not st.session_state.get("x_logged_in"):
        if st.button("Connect Your X Account (Pro Feature)"):
            auth = tweepy.OAuth1UserHandler(
                st.secrets["X_CONSUMER_KEY"],
                st.secrets["X_CONSUMER_SECRET"],
                callback="https://xthreadmaster.streamlit.app"
            )
            try:
                auth_url = auth.get_authorization_url()
                st.session_state.request_token = auth.request_token["oauth_token"]
                st.session_state.request_token_secret = auth.request_token["oauth_token_secret"]
                st.markdown(f"[Login to X]({auth_url})")
            except Exception as e:
                st.error(f"Login setup failed: {e}")

    # Step 4: Logged in
    elif st.session_state.get("x_logged_in"):
        st.success(f"Connected as @{st.session_state.x_username}")
        if st.button("Disconnect X"):
            for key in ["x_access_token", "x_access_secret", "x_username", "x_logged_in"]:
                if key in st.session_state:
                    del st.session_state[key]
            st.success("Disconnected from X")

# Run OAuth
handle_x_oauth()

# === GENERATE ===
if st.button("GENERATE VIRAL THREAD", type="primary", use_container_width=True):
    if topic.strip():
        # === FREE LIMIT ===
        if not pro:
            # Note: File-based limit won't persist in Streamlit Cloud; consider session_state or external DB for production
            limit_file = ".generations"
            if os.path.exists(limit_file):
                with open(limit_file, "r") as f:
                    generations = int(f.read())
            else:
                generations = 0

            if generations >= 3:
                st.error("Free limit: 3/day. Upgrade to Pro for unlimited.")
                with st.expander("Upgrade to Pro ($12/mo)"):
                    st.markdown("**[Buy Now](https://buy.stripe.com/bJe5kEb5R8rm8Gc9pJ28800)**")
                st.stop()

            generations += 1
            with open(limit_file, "w") as f:
                f.write(str(generations))
            remaining = 3 - generations

        # === GENERATE ===
        with st.spinner("Generating thread..."):
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
            response = model.generate_content(prompt)
            thread = response.text.strip()

        st.session_state.thread = thread
        st.session_state.remaining = remaining if not pro else None

    else:
        st.warning("Enter a topic first!")

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
        {thread}
        </div>
        """,
        unsafe_allow_html=True
    )

    st.download_button("📥 Download .txt", thread, "xthread.txt", "text/plain")

    # === AUTO-POST (ONLY PRO + LOGGED IN) ===
    if pro and st.session_state.get("x_logged_in"):
        if st.button("Auto-Post to Your X Account", key="post_x"):
            with st.spinner("Posting..."):
                try:
                    client = tweepy.Client(
                        consumer_key=st.secrets["X_CONSUMER_KEY"],
                        consumer_secret=st.secrets["X_CONSUMER_SECRET"],
                        access_token=st.session_state.x_access_token,
                        access_token_secret=st.session_state.x_access_secret
                    )
                    tweets = thread.split("\n")
                    first = client.create_tweet(text=tweets[0])
                    tweet_id = first.data['id']
                    for t in tweets[1:]:
                        if t.strip():
                            resp = client.create_tweet(in_reply_to_tweet_id=tweet_id, text=t)
                            tweet_id = resp.data['id']
                    url = f"https://x.com/{st.session_state.x_username}/status/{first.data['id']}"
                    st.success(f"Posted! [View on X]({url})")
                except Exception as e:
                    st.error(f"Failed: {e}")

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
