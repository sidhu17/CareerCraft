# app.py — CareerCraft ATS Tracker (Streamlit + Gemini)
# - Reads API key from Streamlit Secrets first, then .env (local)
# - Auto-discovers an available Gemini model and pings it
# - Safe PDF text extraction + prompt size guard
# - Safe image loading (won’t crash if file missing)
# - Built-in diagnostics expander to debug keys/models

import os
from typing import Tuple, Optional

import streamlit as st
from dotenv import load_dotenv
import google.generativeai as genai
import PyPDF2
from PIL import Image

# ───────────────────────────────────────────────────────────────────────────────
# PAGE CONFIG
# ───────────────────────────────────────────────────────────────────────────────
st.set_page_config(page_title="CareerCraft ATS Tracker", layout="wide", page_icon="📄")

# ───────────────────────────────────────────────────────────────────────────────
# ENV & API CONFIG
# ───────────────────────────────────────────────────────────────────────────────
load_dotenv()  # enables local development with .env

def _get_api_key() -> Optional[str]:
    # Prefer Streamlit Secrets (Cloud), then .env (local)
    return (
        st.secrets.get("GEMINI_API_KEY")
        or st.secrets.get("GOOGLE_API_KEY")
        or os.getenv("GEMINI_API_KEY")
        or os.getenv("GOOGLE_API_KEY")
    )

API_KEY = _get_api_key()
if not API_KEY:
    st.error("❌ No API key found. Set `GEMINI_API_KEY` (or `GOOGLE_API_KEY`) in Streamlit Secrets or .env")
    st.stop()

genai.configure(api_key=API_KEY)

# ───────────────────────────────────────────────────────────────────────────────
# DIAGNOSTICS (shows where key came from, SDK version, and visible models)
# ───────────────────────────────────────────────────────────────────────────────
def _mask(k: str) -> str:
    return (k[:6] + "…") if k and len(k) > 6 else "(none)"

API_KEY_SOURCE = (
    "st.secrets[GEMINI_API_KEY]" if "GEMINI_API_KEY" in st.secrets else
    "st.secrets[GOOGLE_API_KEY]" if "GOOGLE_API_KEY" in st.secrets else
    "os.getenv(GEMINI_API_KEY)" if os.getenv("GEMINI_API_KEY") else
    "os.getenv(GOOGLE_API_KEY)" if os.getenv("GOOGLE_API_KEY") else
    "(missing)"
)

with st.expander("🔎 Gemini diagnostics"):
    st.write({"api_key_source": API_KEY_SOURCE, "api_key_sample": _mask(API_KEY)})
    try:
        # google-generativeai exposes __version__ on the module
        st.write({"google-generativeai": getattr(genai, "__version__", "(unknown)")})
    except Exception:
        pass
    # List visible models (if permitted)
    try:
        names = []
        for m in genai.list_models():
            if "generateContent" in getattr(m, "supported_generation_methods", []):
                names.append(getattr(m, "name", ""))
        st.write({"available_models": sorted(names)})
    except Exception as e:
        st.warning("Could not list models (this is fine in some environments).")
        st.exception(e)

# ───────────────────────────────────────────────────────────────────────────────
# MODEL SELECTION (auto-pick a working model for this key)
# ───────────────────────────────────────────────────────────────────────────────
def pick_available_model() -> str:
    prefs = ["gemini-1.5-flash", "gemini-1.5-pro", "gemini-1.5-flash-8b", "gemini-1.0-pro"]
    try:
        avail = []
        for m in genai.list_models():
            if "generateContent" in getattr(m, "supported_generation_methods", []):
                name = getattr(m, "name", "")
                if name:
                    avail.append(name)
        # Prefer by our list
        for p in prefs:
            if p in avail:
                return p
        # Fallback to first generative model if present
        if avail:
            return avail[0]
    except Exception:
        # If listing fails (some envs), probe common names directly
        pass

    for p in ["gemini-1.5-pro", "gemini-1.5-flash", "gemini-1.0-pro"]:
        try:
            genai.GenerativeModel(p).generate_content("ping")
            return p
        except Exception:
            continue

    raise RuntimeError("No usable Gemini model for this API key.")

try:
    MODEL_NAME = pick_available_model()
    st.info(f"Using model: **{MODEL_NAME}**")
    model = genai.GenerativeModel(MODEL_NAME)
    # Quick ping to surface NOT_FOUND immediately
    _ = model.generate_content("ping")
except Exception as e:
    st.error("❌ Could not initialize a Gemini model. (Model name / key / quota / region issue.)")
    st.exception(e)
    st.stop()

# ───────────────────────────────────────────────────────────────────────────────
# UTILITIES
# ───────────────────────────────────────────────────────────────────────────────
def load_and_resize(path: str, size: Tuple[int, int]) -> Optional[Image.Image]:
    """Load image from disk and resize to `size` (width, height). Return None if missing."""
    try:
        img = Image.open(path)
        return img.resize(size)
    except Exception:
        st.info(f"ℹ️ Image not found or could not be loaded: `{path}`")
        return None

def safe_show_image(path: str, size: Tuple[int, int]):
    img = load_and_resize(path, size)
    if img is not None:
        st.image(img)

def input_pdf_text(pdf_file) -> str:
    """
    Extract text from a PDF file-like object using PyPDF2.
    Returns a concatenated string of all pages.
    """
    try:
        if hasattr(pdf_file, "read"):
            reader = PyPDF2.PdfReader(pdf_file)
        else:
            with open(pdf_file, "rb") as f:
                reader = PyPDF2.PdfReader(f)
        texts = []
        for page in reader.pages:
            texts.append(page.extract_text() or "")
        return "".join(texts)
    except Exception as e:
        st.error("❌ Failed to read the PDF. Ensure it is a valid, text-based PDF.")
        st.exception(e)
        return ""

def truncate(text: str, max_chars: int = 15000) -> str:
    """Guard against overly long prompts (keeps app snappy and avoids size limits)."""
    if text and len(text) > max_chars:
        return text[:max_chars] + "\n\n[...truncated due to length...]"
    return text

def get_gemini_response(prompt: str) -> str:
    try:
        resp = model.generate_content(prompt)
        return getattr(resp, "text", "") or "No text returned."
    except Exception as e:
        st.error("⚠️ Gemini request failed (often model name / quota / prompt size).")
        st.exception(e)
        return "Gemini request failed. See error above."

# ───────────────────────────────────────────────────────────────────────────────
# UI — INTRODUCTION
# ───────────────────────────────────────────────────────────────────────────────
intro_col, img_col = st.columns([3, 1], gap="large")
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
    # uniform 200×200px icon
    safe_show_image("images/icon_dashboard.png", (200, 200))

st.markdown("---")

# ───────────────────────────────────────────────────────────────────────────────
# UI — OFFERINGS
# ───────────────────────────────────────────────────────────────────────────────
offer_img, offer_text = st.columns([1, 2], gap="medium")
with offer_img:
    # uniform 180×180px offering graphic
    safe_show_image("images/offerings.png", (180, 180))
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

# ───────────────────────────────────────────────────────────────────────────────
# UI — RESUME ATS TRACKING
# ───────────────────────────────────────────────────────────────────────────────
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
                if not resume_text.strip():
                    st.warning("Could not extract text from the PDF. Try a text-based resume PDF.")
                else:
                    # keep prompt size within safe bounds
                    jd_text = truncate(job_desc, 7000)
                    cv_text = truncate(resume_text, 9000)

                    prompt = (
                        "You are an ATS expert. Compare the job description and resume.\n"
                        "Return a structured, concise analysis with:\n"
                        "1) Overall match percentage (as a number 0–100)\n"
                        "2) Missing or weak keywords/skills (bulleted)\n"
                        "3) A punchy 3–5 sentence profile summary tailored to the JD\n"
                        "4) Actionable suggestions to improve alignment (bulleted)\n"
                        "Keep the tone objective and specific.\n\n"
                        f"--- JOB DESCRIPTION ---\n{jd_text}\n\n"
                        f"--- RESUME ---\n{cv_text}\n"
                    )

                    st.markdown("### 📊 Analysis Result")
                    st.write(get_gemini_response(prompt))

with col2:
    # uniform 240×180px analysis graphic
    safe_show_image("images/analysis.png", (240, 180))

st.markdown("---")

# ───────────────────────────────────────────────────────────────────────────────
# UI — FAQ
# ───────────────────────────────────────────────────────────────────────────────
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
    st.write("A: Absolutely—just fork the GitHub repo and configure secrets or `.env`.")
with faq_col1:
    # uniform 200×200px FAQ graphic
    safe_show_image("images/faq.png", (200, 200))