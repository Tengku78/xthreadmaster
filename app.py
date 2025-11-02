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

# === EMAIL INPUT (OUTSIDE BUTTON) ===
email = st.text_input("Enter your email (for Pro unlock)", placeholder="your@email.com")

# === INPUTS ===
col1, col2 = st.columns(2)
with col1:
    topic = st.text_input("Topic/Niche", placeholder="AI side hustles, fitness tips, etc.")
with col2:
    tone = st.selectbox("Tone", ["Casual", "Professional", "Funny", "Inspirational", "Degen"])

length = st.slider("Thread Length", 5, 15, 8, help="Number of tweets")

# === STRIPE PRO CHECK ===
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
        # === FREE TIER LIMIT (FILE-BASED) ===
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

            # Increment after generation
            generations += 1
            with open(limit_file, "w") as f:
                f.write(str(generations))
            remaining = 3 - generations
            st.success(f"Thread ready! ({remaining} free left today)")

        # === GENERATE THREAD ===
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
            - NO NUMBERING (no 1/, 2/, etc.)
            - JUST THE TEXT, ONE TWEET PER LINE
            OUTPUT ONLY THE THREAD.
            """
            response = model.generate_content(prompt)
            thread = response.text.strip()
            
            # === FULL WIDTH, TALL, SCROLLABLE THREAD BOX ===
            st.markdown(
                f"""
                <div style="
                    background-color: #1a1a1a;
                    color: #ffffff;
                    border-radius: 12px;
                    border: 1px solid #e0e0e0;
                    font-family: 'Courier New', monospace;
                    font-size: 15px;
                    line-height: 1.6;
                    max-height: 500px;
                    overflow-y: auto;
                    white-space: pre-wrap;
                    word-wrap: break-word;
                ">
                {thread}
                </div>
                """,
                unsafe_allow_html=True
            )
            st.code(thread, language=None)
            
            # === PRO FEATURES ===
            if pro:
                st.success("Pro Thread Ready – Unlimited!")
                if st.button("Post to X (Pro Feature)"):
                    st.write("Auto-post coming in v2!")
                    st.balloons()

        # === UPSELL (FREE USERS ONLY) ===
        if not pro:
            with st.expander("Go PRO: Unlimited + Auto-Post ($12/mo)"):
                st.markdown("**[Buy Now](https://buy.stripe.com/bJe5kEb5R8rm8Gc9pJ28800)**")

    else:
        st.warning("Enter a topic first!")

# === FOOTER ===
st.markdown("---")
st.caption("**Built with Grok & Streamlit** | First $100 MRR = beer on me.")
