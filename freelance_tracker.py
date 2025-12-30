import sys
import os
import time
import datetime
import cloudscraper
from bs4 import BeautifulSoup
import requests
from google import genai

# ==========================================
# ⚙️ إعدادات السيرفر
# ==========================================

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# إعداد العميل
ai_client = None

if GEMINI_API_KEY:
    try:
        ai_client = genai.Client(api_key=GEMINI_API_KEY.strip())
        print("✅ GenAI Client Connected successfully.")
    except Exception as e:
        print(f"❌ Client Error: {e}")

# --- الكلمات المفتاحية ---
EXCLUDED_KEYWORDS = [
    "wordpress", "ووردبريس", "وردبريس", "ورد بريس", 
    "elementor", "divi", "woocommerce", "وكومرس", 
    "shopify", "شوبيفاي", "سلة", "زد", "salla", "zid",
    "blogger", "بلوجر", "logo", "لوجو", "بانر", "شعار"
]

WEB_KEYWORDS = [
    "web", "ويب", "موقع", "site", "front", "back", 
    "full stack", "full-stack", "php", "laravel", 
    "python", "django", "node", "react", "vue", 
    "api", "sql", "server", "سيرفر", "استضافة", 
    "رفع", "deploy", "javascript", "js", "html", 
    "css", "لوحة تحكم", "dashboard", "next.js", 
    "next", "nextjs", "صفحة هبوط", "landing page"
]

CREATIVE_KEYWORDS = [
    "تصميم", "design", "جرافيك", "graphic", 
    "مونتاج", "montage", "edit", "video", 
    "فيديو", "موشن", "فوتوشوب", "photoshop", 
    "premiere", "بريمير", "ريلز", "reels"
]

QURAN_KEYWORDS = [
    "قرآن", "قران", "قرءان", "quran", 
    "تلاوة", "recitation", "مصحف", "تجويد", 
    "آية", "اية", "ايه", "آيات", "سورة", 
    "ديني", "دعوي", "إسلامي", "islamic"
]

URLS = {
    "Mostaql": "https://mostaql.com/projects",
    "Khamsat": "https://khamsat.com/community/requests"
}
POLL_INTERVAL = 60
processed_projects = set()

scraper = cloudscraper.create_scraper(
    browser={'browser': 'chrome', 'platform': 'windows', 'desktop': True}
)
scraper.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept-Language': 'ar,en-US;q=0.9,en;q=0.8'
})

def get_full_project_details(link, source):
    try:
        response = scraper.get(link, timeout=15)
        if response.status_code != 200: return None
        soup = BeautifulSoup(response.content, 'html.parser')
        
        description = ""
        if source == "Mostaql":
            desc_elem = soup.select_one('#project-brief-section') or soup.select_one('.project-desc') or soup.select_one('.card-body')
            if desc_elem: description = desc_elem.text.strip()
        elif source == "Khamsat":
            desc_elem = soup.select_one('.article-body') or soup.select_one('.post_content')
            if desc_elem: description = desc_elem.text.strip()
            
        return description[:2500] 
    except Exception as e:
        print(f"   ❌ Detail Fetch Error: {e}")
        return None

def generate_smart_response(title, description):
    """
    يستخدم الموديلات الموجودة في حسابك بالضبط لتجنب خطأ 404
    """
    if not ai_client: return "⚠️ AI Service Unavailable"
    
    # هذه القائمة مأخوذة من الصورة التي أرسلتها (دقيقة 100%)
    models_to_try = [
        "gemini-2.5-pro",
        "gemini-2.5-flash", 
        "gemini-2.0-flash",       
        "gemini-2.0-flash-lite",  
        "gemini-3-flash-preview"
    ]

    prompt = f"""
    Act as an expert Senior Full Stack Developer and Freelancer.
    
    Project Details:
    - Title: {title}
    - Description: {description}

    Instructions:
    1. Read the project description carefully to understand the client's specific needs (do not rely on the title only).
    2. Write a professional, detailed, and convincing proposal in Arabic. 
       - Do not make it short or generic. 
       - Explain how you will solve their specific problem based on the description.
       - Show enthusiasm and expertise.
    3. At the very end, provide a realistic estimation for the Cost (in USD) and Duration (in Days) based on the scope of work described.

    Required Output Format:
    [The Proposal Text in Arabic]
    ــــــــــــــــــــــــــ
    💡 *التقدير:* [Price] | [Duration]
    """
    
    for model_name in models_to_try:
        try:
            # print(f"   🔄 Trying: {model_name}...") # (اختياري للتتبع)
            response = ai_client.models.generate_content(
                model=model_name, 
                contents=prompt
            )
            print(f"   ✅ Success using: {model_name}")
            return response.text
        except Exception as e:
            # لو فشل نجرب اللي بعده بصمت
            continue

    return "تعذر توليد الرد من جميع الموديلات المتاحة."

def send_telegram_message(title, link, source, category):
    if not BOT_TOKEN or not CHAT_ID: 
        print("🛑 Error: Missing Telegram Tokens")
        return

    description = get_full_project_details(link, source)
    if not description: description = title 

    ai_text = generate_smart_response(title, description)

    # 1. إزالة التنسيق مؤقتاً لضمان وصول الرسالة (سناقوم بإرجاعه لاحقاً بطريقة آمنة)
    # لاحظ أنني حذفت "parse_mode": "Markdown" من الأسفل
    msg = f"""🔔 مشروع {category} جديد ({source})

📝 {title}

🔗 {link}

ــــــــــــــــــــــــــــــــــــــــــــــــــــ
{ai_text}
"""
    
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    # قمنا بإزالة parse_mode مؤقتاً
    payload = {"chat_id": CHAT_ID, "text": msg} 
    
    try:
        response = requests.post(url, data=payload)
        
        # 2. التحقق الدقيق من رد تليجرام
        if response.status_code == 200:
            print(f"   ✅ Notification Sent Successfully: {title}")
        else:
            # هنا سيظهر لك السبب الحقيقي إذا لم تصل الرسالة
            print(f"   ⚠️ Telegram Error: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"   ❌ Network Error: {e}")

def check_project_filter(title):
    text = title.lower()
    if any(w in text for w in EXCLUDED_KEYWORDS): return None
    if any(w in text for w in WEB_KEYWORDS): return "ويب 💻"
    is_creative = any(w in text for w in CREATIVE_KEYWORDS)
    is_quran = any(w in text for w in QURAN_KEYWORDS)
    if is_creative and is_quran: return "قرآن 🕌"
    return None

def scrape_site(source_name, url, is_first_run=False):
    print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Checking {source_name}...", end=" ")
    try:
        response = scraper.get(url, timeout=30)
        if response.status_code != 200:
            print(f"HTTP Error: {response.status_code}")
            return

        soup = BeautifulSoup(response.content, 'html.parser')
        projects = []

        if source_name == "Mostaql":
            rows = soup.select('tr.project-row h2 a, .project-title a, h2 a')
            for t_elem in rows:
                if t_elem:
                    title = t_elem.text.strip()
                    href = t_elem['href']
                    link = "https://mostaql.com" + href if not href.startswith("http") else href
                    projects.append((title, link))
        
        elif source_name == "Khamsat":
            links = soup.find_all('a', href=True)
            for t in links:
                href = t['href']
                if "/community/requests/" in href and any(c.isdigit() for c in href):
                    title = t.text.strip()
                    if len(title) < 5: continue
                    link = "https://khamsat.com" + href if not href.startswith("http") else href
                    if not any(p[1] == link for p in projects): 
                        projects.append((title, link))

        print(f"-> Found {len(projects)}")

        for title, link in projects:
            if link in processed_projects: continue
            
            if is_first_run:
                processed_projects.add(link)
                continue
            
            cat = check_project_filter(title)
            if cat:
                print(f"   🔥 Match: {title}")
                send_telegram_message(title, link, source_name, cat)
            
            processed_projects.add(link)
            
    except Exception as e:
        print(f"\n❌ Scraping Error: {e}")

def main():
    print("--- 🤖 Freelance Bot (Smart Edition V3) ---")
    
    if not BOT_TOKEN or not CHAT_ID:
        print("🛑 Missing Tokens!")
        return

    print("1. Initializing & caching existing projects...")
    for src, url in URLS.items(): scrape_site(src, url, is_first_run=True)
    
    print(f"\n✅ Ready! Watching for new projects...")
    
    while True:
        try:
            for src, url in URLS.items(): scrape_site(src, url, is_first_run=False)
            time.sleep(POLL_INTERVAL)
        except Exception as e:
            print(f"Main Loop Error: {e}")
            time.sleep(POLL_INTERVAL)

if __name__ == "__main__":
    main()