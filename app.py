import google.generativeai as genai

# ✅ Step 1: Replace with your actual API key from Google Cloud Console
genai.configure(api_key="AIzaSyCA6D0FIK9ZuvqSRO0lq6YGsCYiH3eh45k")

# ✅ Step 2: Correct model name with v1 structure
model = genai.GenerativeModel(model_name="models/gemini-pro")

print(model._client.__class__)

# ✅ Step 3: Generate a test output
response = model.generate_content("Give a quick overview of AI in job hiring.")
print(response.text)