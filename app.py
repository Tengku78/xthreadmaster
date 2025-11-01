import streamlit as st
import google.generativeai as genai
import requests

# === CONFIG ===
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
model = genai.GenerativeModel('gemini-2.0-flash')

st.set_page_config(page_title="XThreadMaster", page_icon="rocket", layout="centered")
st.title("XThreadMaster – Viral X Threads in 10s")
st.markdown("**Enter topic → Get full thread (hook, value, CTA) – Copy & Post!**")

# === INPUTS ===
col1, col2 = st.columns(2)
with col1:
    topic = st.text_input("Topic/Niche", placeholder="AI side hustles, fitness tips, etc.")
with col2:
    tone = st.selectbox("Tone", ["Casual", "Professional", "Funny", "Inspirational", "Degen"])

length = st.slider("Thread Length", 5, 15, 8, help="Number of tweets")

# === STRIPE PRO CHECK (via email) ===
def is_pro_user():
    email = st.text_input("Enter your email (for Pro unlock)", key="email_input")
    if email:
        try:
            # Check if email has active subscription
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
                    st.session_state.pro = True
                    st.success(f"Pro unlocked for {email}!")
                    return True
            st.warning("No active Pro subscription found.")
        except:
            st.error("Pro check failed. Try again.")
    return False

# === GENERATE ===
if st.button("GENERATE VIRAL THREAD", type="primary", use_container_width=True):
    if topic.strip():
        # Check Pro status
        pro = st.session_state.get("pro", False) or is_pro_user()
        
        # Free limit
        if not pro:
            if "generations" not in st.session_state:
                st.session_state.generations = 0
                st.session_state.daily_limit = 3
            if st.session_state.generations >= st.session_state.daily_limit:
                st.error("Free limit reached (3/day)! Upgrade to Pro.")
                with st.expander("Go PRO: Unlimited ($12/mo)"):
                    st.markdown("**[Buy Now](https://buy.stripe.com/bJe5kEb5R8rm8Gc9pJ28800)**")
                st.stop()

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
            - Numbered 1/ 2/
            OUTPUT ONLY THE THREAD.
            """
            response = model.generate_content(prompt)
            thread = response.text.strip()
            
            if not pro:
                st.session_state.generations += 1
                remaining = st.session_state.daily_limit - st.session_state.generations
                st.success(f"Thread ready! ({remaining} free left)")
            else:
                st.success("Pro Thread Ready – Unlimited!")
            
            st.markdown(f"```markdown\n{thread}\n```")
            st.code(thread, language=None)
            
            # Auto-post button (Pro only)
            if pro:
                if st.button("Post to X (Pro)"):
                    st.write("X posting coming in v2!")
                    st.balloons()

        # Upsell
        if not pro:
            with st.expander("Go PRO: Unlimited + Auto-Post ($12/mo)"):
                st.markdown("**[Buy Now](https://buy.stripe.com/bJe5kEb5R8rm8Gc9pJ28800)**")
                st.caption("Cancel anytime.")

    else:
        st.warning("Enter a topic!")

# === FOOTER ===
st.markdown("---")
st.caption("**Built with Grok & Streamlit** | First $100 MRR = beer on me.")
