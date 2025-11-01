import streamlit as st
import google.generativeai as genai  # ← THIS LINE WAS MISSING!

# === CONFIG (LOCAL TESTING) ===
genai.configure(api_key="AIzaSyBQVIGzuFi-gaCP1g7EB3dFELE2Mi0yCvc")

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

# === GENERATE ===
if st.button("GENERATE VIRAL THREAD", type="primary", use_container_width=True):
    if topic.strip():
        with st.spinner("Cooking viral thread..."):
            model = genai.GenerativeModel('gemini-2.0-flash')
            
            prompt = f"""
            Write a VIRAL X (Twitter) thread about: "{topic}"
            - {length} tweets
            - Tone: {tone}
            - Tweet 1: Killer hook (question, bold stat, or shock)
            - Middle: 3-5 value bombs, tips, stories
            - Last: Strong CTA (follow, RT, comment)
            - Use emojis EVERYWHERE
            - Numbered: 1/ 2/ etc.
            - <100 chars per tweet
            - Make it ENGAGING & shareable
            OUTPUT ONLY THE THREAD.
            """
            
            response = model.generate_content(prompt)
            thread = response.text.strip()
            
            st.success("Your Viral Thread – Copy & Post!")
            st.markdown(f"```markdown\n{thread}\n```")
            st.code(thread, language=None)

            # === PRO UPSELL ===
            with st.expander("Go PRO: Unlimited + Scheduler ($9/mo)"):
                st.markdown("**[Buy Now – Instant Access](https://buy.stripe.com/test_123)**")
                st.caption("Pro: No limits, auto-post to X, analytics")
    else:
        st.warning("Enter a topic first!")

# === FOOTER ===
st.markdown("---")
st.caption("**Built in 30 mins with Grok & Streamlit** | Share your first $100 MRR!")