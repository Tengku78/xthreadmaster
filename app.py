import streamlit as st
import google.generativeai as genai
import requests
import os

# === CONFIG ===
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
model = genai.GenerativeModel('gemini-2.0-flash')

st.set_page_config(page_title="XThreadMaster", page_icon="rocket", layout="centered")
st.title("XThreadMaster – Viral X Threads in 10s")
st.markdown("**Enter topic → Get full thread (hook, value, CTA) – Copy & Post!**")

# === EMAIL INPUT ===
email = st.text_input("Enter your email (for Pro unlock)", placeholder="your@email.com")

# === INPUTS ===
col1, col2 = st.columns(2)
with col1:
    topic = st.text_input("Topic/Niche", placeholder="AI side hustles, fitness tips, etc.")
with col2:
    tone = st.selectbox("Tone", ["Casual", "Professional", "Funny", "Inspirational", "Degen"])

length = st.slider("Thread Length", 5, 15, 8, help="Number of tweets")

# === PRO CHECK — MOVED UP HERE! ===
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
if pro:
    st.success(f"Pro unlocked for {email}! Unlimited access.")
elif email:
    st.warning("No active Pro subscription. Using free tier.")

# === GENERATE ===
if st.button("GENERATE VIRAL THREAD", type="primary", use_container_width=True):
    if topic.strip():
        # === FREE LIMIT ===
        if not pro:
            limit_file = ".generations"
            if os.path.exists(limit_file):
                with open(limit_file, "r") as f:
                    generations = int(f.read())
            else:
                generations = 0

            if generations >= 3:
                st.error("Free limit reached (3/day)! Upgrade to Pro.")
                with st.expander("Go PRO: Unlimited ($12/mo)"):
                    st.markdown("**[Buy Now](https://buy.stripe.com/bJe5kEb5R8rm8Gc9pJ28800)**")
                st.stop()

            generations += 1
            with open(limit_file, "w") as f:
                f.write(str(generations))
            remaining = 3 - generations

        # === GENERATE ===
        with st.spinner("Cooking viral thread..."):
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

        # === SAVE TO SESSION ===
        st.session_state.thread = thread
        st.session_state.remaining = remaining if not pro else None

    else:
        st.warning("Enter a topic first!")

# === DISPLAY THREAD + PRO FEATURES ===
if "thread" in st.session_state:
    thread = st.session_state.thread

    # === DARK BOX ===
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

    # === DOWNLOAD BUTTON ===
    st.download_button(
        label="📥 Download .txt",
        data=thread,
        file_name="xthread.txt",
        mime="text/plain"
    )

    # === AUTO-POST BUTTON (ONLY FOR PRO) ===
    if pro:
        if st.button("Auto-Post to X", key="post_x"):
            with st.spinner("Posting to X..."):
                try:
                    import tweepy
                    client = tweepy.Client(
                        consumer_key=st.secrets["X_CONSUMER_KEY"],
                        consumer_secret=st.secrets["X_CONSUMER_SECRET"],
                        access_token=st.secrets["X_ACCESS_TOKEN"],
                        access_token_secret=st.secrets["X_ACCESS_SECRET"]
                    )
                    # Post first tweet
                    first_tweet = thread.split("\n")[0]
                    response = client.create_tweet(text=first_tweet)
                    tweet_id = response.data['id']
                    # Post rest as thread
                    for line in thread.split("\n")[1:]:
                        if line.strip():
                            response = client.create_tweet(in_reply_to_tweet_id=tweet_id, text=line)
                            tweet_id = response.data['id']
                    
                    thread_url = f"https://x.com/tengku5181/status/{response.data['id']}"
                    st.success(f"Thread posted! [View on X]({thread_url})")
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
        with st.expander("Go PRO: Unlimited ($12/mo)"):
            st.markdown("**[Buy Now](https://buy.stripe.com/bJe5kEb5R8rm8Gc9pJ28800)**")

# === FOOTER ===
st.markdown("---")
st.caption("**Built with Grok & Streamlit** | First $100 MRR = beer on me.")
