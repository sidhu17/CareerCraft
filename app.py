import os
import streamlit as st
from dotenv import load_dotenv
import PyPDF2
import google.generativeai as genai
from PIL import Image

# ─── CONFIG & BACKGROUND ──────────────────────────────────────────────────────
try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
except KeyError:
    st.error("❌ GEMINI_API_KEY not found in Streamlit secrets")
    st.stop()

st.set_page_config(page_title="CareerCraft ATS Tracker", layout="wide", page_icon="📄")

# configure Gemini
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

# ─── IMAGE HELPER ──────────────────────────────────────────────────────────────
def load_and_resize(path: str, size: tuple[int,int]) -> Image.Image:
    """Load image from disk and resize to `size` (width, height)."""
    img = Image.open(path)
    return img.resize(size)

# ─── HELPERS ──────────────────────────────────────────────────────────────────
def get_gemini_response(prompt: str) -> str:
    return model.generate_content(prompt).text

def input_pdf_text(pdf_file) -> str:
    reader = PyPDF2.PdfReader(pdf_file)
    return "".join(page.extract_text() or "" for page in reader.pages)

# ─── 1. INTRODUCTION ───────────────────────────────────────────────────────────
intro_col, img_col = st.columns([3, 1], gap="large")
with intro_col:
    st.title("🎯 CareerCraft")
    st.header("ATS‑Optimized Resume Analyzer")
    st.markdown(
        """
        CareerCraft empowers you to optimize and track your resume
        against any job description using Google’s Gemini AI.
        Upload your resume, paste the job description, and instantly
        receive a match percentage, missing keywords, and a punchy summary.
        """
    )
with img_col:
    # uniform 200×200px icon
    st.image(load_and_resize("images/icon_dashboard.png", (200, 200)))

st.markdown("---")

# ─── 2. OFFERINGS ──────────────────────────────────────────────────────────────
offer_img, offer_text = st.columns([1, 2], gap="medium")
with offer_img:
    # uniform 180×180px offering graphic
    st.image(load_and_resize("images/offerings.png", (180, 180)))
with offer_text:
    st.subheader("🚀 Wide Range of Offerings")
    st.markdown(
        """
        - **ATS‑Optimized Resume Analysis**  
        - **Resume Optimization Suggestions**  
        - **Skill & Keyword Enhancement**  
        - **Profile Summary Generator**  
        - **Interactive Match Dashboard**  
        - **Downloadable Reports**  
        """
    )

st.markdown("---")

# ─── 3. RESUME ATS TRACKING ────────────────────────────────────────────────────
col1, col2 = st.columns(2, gap="large")
with col1:
    st.subheader("📂 Analyze Your Resume")
    job_desc = st.text_area("Paste the **Job Description** here:", height=150)
    uploaded_resume = st.file_uploader("Upload your **Resume (PDF)**:", type=["pdf"])
    if st.button("🔍 Submit for Analysis"):
        if not job_desc:
            st.warning("Please paste a job description.")
        elif not uploaded_resume:
            st.warning("Please upload your resume PDF.")
        else:
            with st.spinner("Reading resume & calling Gemini..."):
                resume_text = input_pdf_text(uploaded_resume)
                prompt = (
                    "You are an ATS expert. Compare the job description and resume. "
                    "Provide:\n1. % match\n2. Missing keywords/skills\n3. Profile summary\n\n"
                    f"**Job Description:**\n{job_desc}\n\n**Resume:**\n{resume_text}"
                )
                st.markdown("### 📊 Analysis Result")
                st.write(get_gemini_response(prompt))
with col2:
    # uniform 240×180px analysis graphic
    st.image(load_and_resize("images/analysis.png", (240, 180)))

st.markdown("---")

# ─── 4. FAQ ───────────────────────────────────────────────────────────────────
faq_col1, faq_col2 = st.columns(2, gap="large")
with faq_col2:
    st.subheader("❓ Frequently Asked Questions")
    st.write("**Q:** What is CareerCraft?") 
    st.write("A: A Gemini-powered ATS resume analyzer.") 
    st.write("**Q:** How many analyses can I run?") 
    st.write("A: Up to 50/day free tier, 15/minute.") 
    st.write("**Q:** Is my data secure?") 
    st.write("A: Yes, nothing is stored after you close the app.") 
    st.write("**Q:** Can I deploy my own?") 
    st.write("A: Absolutely—just fork the GitHub repo and configure `.env`.") 
with faq_col1:
    # uniform 200×200px FAQ graphic
    st.image(load_and_resize("images/faq.png", (200, 200)))