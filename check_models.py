import google.generativeai as genai
import os

# ضع مفتاحك هنا مباشرة للتجربة
API_KEY = "ضع_مفتاحك_هنا"

genai.configure(api_key=API_KEY)

print("الموديلات المتاحة لمفتاحك:")
for m in genai.list_models():
    if 'generateContent' in m.supported_generation_methods:
        print(f"- {m.name}")