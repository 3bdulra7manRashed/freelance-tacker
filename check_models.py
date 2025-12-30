import os
import google.genai as genai

# =========================
# 🔑 إعداد مفتاح Gemini
# =========================
GEMINI_API_KEY = "AIzaSyD8_5oNQnZl7R62blz3xZ9BlUwGAqJsfAw"

if not GEMINI_API_KEY:
    print("❌ GEMINI_API_KEY not set in environment variables.")
    exit()

client = genai.Client(api_key=GEMINI_API_KEY)

print("\n📃 Available Models:\n")

try:
    for model in client.models.list():
        print(" -", model.name)
except Exception as e:
    print("❌ Error listing models:", e)