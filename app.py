import streamlit as st
import google.generativeai as genai  # ← THIS LINE WAS MISSING!

# === CONFIG (LOCAL TESTING) ===
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

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

# === GENERATE WITH LIMITS ===
if st.button("GENERATE VIRAL THREAD", type="primary", use_container_width=True):
    if topic.strip():
        # Free limit: 3 per day (session-based for MVP)
        if "generations" not in st.session_state:
            st.session_state.generations = 0
            st.session_state.daily_limit = 3
        
        if st.session_state.generations < st.session_state.daily_limit:
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
                
                st.session_state.generations += 1
                remaining = st.session_state.daily_limit - st.session_state.generations
                
                st.success(f"Your Viral Thread – Copy & Post! ({remaining} free left today)")
                st.markdown(f"```markdown\n{thread}\n```")
                st.code(thread, language=None)
                
                if remaining > 0:
                    st.info(f"Free generations left today: {remaining}/3")
                else:
                    st.warning("Daily free limit reached! Upgrade for unlimited.")
                
                # PRO UPSELL (always show, but urgent when limited)
                with st.expander("🔒 Go PRO: Unlimited + Scheduler ($9/mo)"):
                    st.markdown("**Pro Features:**")
                    st.markdown("- Unlimited threads (no daily limits)")
                    st.markdown("- Auto-post scheduler to X")
                    st.markdown("- Image generation for threads")
                    st.markdown("- Analytics dashboard")
                    st.markdown("**[Buy Now – Instant Access](https://buy.stripe.com/bJe5kEb5R8rm8Gc9pJ28800)**")
                    st.caption("Cancel anytime. First month $4.50 intro offer.")
        else:
            st.error("🚫 Daily free limit reached (3 threads)! Upgrade for unlimited.")
            with st.expander("🔒 Go PRO: Unlimited + Extras ($9/mo)"):
                st.markdown("**Why Pro?** Free tier = 3/day. Pro = endless + tools.")
                st.markdown("**[Upgrade Now](https://buy.stripe.com/bJe5kEb5R8rm8Gc9pJ28800)**")
    else:
        st.warning("Enter a topic first!")

# === FOOTER ===
st.markdown("---")
st.caption("**Built in 30 mins with Grok & Streamlit** | Share your first $100 MRR!")
