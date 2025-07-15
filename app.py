# app.py

import os
from dotenv import load_dotenv
import streamlit as st
import PyPDF2
import google.generativeai as genai
from PIL import Image

# ─── CONFIG & INITIALIZATION ─────────────────────────────────────────────────

load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY:
    st.error("❌ GEMINI_API_KEY missing in .env")
    st.stop()

genai.configure(api_key=API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")  # switch to "gemini-1.5-pro" if you have quota

st.set_page_config(
    page_title="CareerCraft ATS Tracker",
    layout="wide",
    page_icon="📄"
)

# ─── HELPERS ──────────────────────────────────────────────────────────────────

def get_gemini_response(prompt: str) -> str:
    """Call Gemini and return its text response."""
    resp = model.generate_content(prompt)
    return resp.text

def input_pdf_text(pdf_file) -> str:
    """Extract all text from an uploaded PDF."""
    reader = PyPDF2.PdfReader(pdf_file)
    text = ""
    for page in reader.pages:
        text += page.extract_text() or ""
    return text

# ─── 1. INTRODUCTION ───────────────────────────────────────────────────────────

intro_col, img_col = st.columns([3,1])
with intro_col:
    st.title("🎯 CareerCraft")
    st.header("ATS-Optimized Resume Analyzer")
    st.markdown(
        """
        CareerCraft empowers you to optimize and track your resume
        against any job description using Google’s Gemini AI.
        Upload your resume, paste the job description, and instantly
        receive a match percentage, missing keywords, and a punchy summary.
        """
    )
with img_col:
    st.image("images/icon_dashboard.png", caption="Career at a glance", use_container_width=True)

st.markdown("---")

# ─── 2. OFFERINGS ──────────────────────────────────────────────────────────────

offer_img, offer_text = st.columns([1,2])
with offer_img:
    st.image("images/offerings.png", use_container_width=True)
with offer_text:
    st.subheader("🚀 Wide Range of Offerings")
    st.markdown(
        """
        - **ATS-Optimized Resume Analysis**  
        - **Resume Optimization Suggestions**  
        - **Skill & Keyword Enhancement**  
        - **Profile Summary Generator**  
        - **Interactive Match Dashboard**  
        - **Downloadable Reports**  
        """
    )

st.markdown("---")

# ─── 3. RESUME ATS TRACKING ────────────────────────────────────────────────────

col1, col2 = st.columns(2)
with col1:
    st.subheader("📂 Analyze Your Resume")
    job_desc = st.text_area("Paste the **Job Description** here:", height=150)
    uploaded_resume = st.file_uploader("Upload your **Resume (PDF)**:", type=["pdf"])
    if st.button("🔍 Submit for Analysis"):
        if not job_desc:
            st.write("")  # vertical space
            st.warning("Please paste a job description.")
        elif not uploaded_resume:
            st.write("")  # vertical space
            st.warning("Please upload your resume PDF.")
        else:
            with st.spinner("Reading resume & calling Gemini..."):
                resume_text = input_pdf_text(uploaded_resume)
                prompt = (
                    "You are an ATS expert. Compare the job description and resume. "
                    "Provide:\n"
                    "1. % match\n"
                    "2. Missing keywords/skills\n"
                    "3. Profile summary\n\n"
                    f"**Job Description:**\n{job_desc}\n\n**Resume:**\n{resume_text}"
                )
                result = get_gemini_response(prompt)
            st.markdown("### 📊 Analysis Result")
            st.write(result)

with col2:
    st.image("images/analysis.png", caption="Your career path", use_container_width=True)

st.markdown("---")

# ─── 4. FAQ ───────────────────────────────────────────────────────────────────

faq_col1, faq_col2 = st.columns(2)
with faq_col2:
    st.subheader("❓ Frequently Asked Questions")
    st.write("**Q:** What is CareerCraft?") 
    st.write("A: A Gemini-powered ATS resume analyzer.") 
    st.write("")  # vertical space
    st.write("**Q:** How many analyses can I run?") 
    st.write("A: Up to 50/day free tier, 15/minute.") 
    st.write("")  # vertical space
    st.write("**Q:** Is my data secure?") 
    st.write("A: Yes, nothing is stored after you close the app.") 
    st.write("")  # vertical space
    st.write("**Q:** Can I deploy my own?") 
    st.write("A: Absolutely—just fork the GitHub repo and configure `.env`.") 
with faq_col1:
    st.image("images/faq.png", caption="Need help?", use_container_width=True)

# ─── FOOTER / HOSTING INSTRUCTIONS ────────────────────────────────────────────

st.markdown("---")
st.markdown(
    """
    **Hosting & Running**  
    1. Install dependencies:  
       `pip install -r requirements.txt`  
    2. Add your key to `.env` (no quotes).  
    3. Launch with:  
       `streamlit run app.py`
    """
)