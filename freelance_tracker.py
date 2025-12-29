import sys
import os
import time
import datetime
import importlib
import cloudscraper
from bs4 import BeautifulSoup
import requests

# --- 1. إعدادات الأمان (القراءة من السيرفر مباشرة) ---
# الكود سيقوم بالبحث عن هذه القيم في إعدادات Coolify
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

URLS = {
    "Mostaql": "https://mostaql.com/projects",
    "Khamsat": "https://khamsat.com/community/requests"
}

POLL_INTERVAL = 120
processed_projects = set()

# إعداد المتصفح الوهمي لتخطي الحماية
scraper = cloudscraper.create_scraper(
    browser={'browser': 'chrome', 'platform': 'windows', 'desktop': True}
)

# --- 2. الفلاتر ---
EXCLUDED_KEYWORDS = ["wordpress", "ووردبريس", "وردبريس", "ورد بريس", "elementor", "divi", "woocommerce", "وكومرس", "shopify", "شوبيفاي", "سلة", "زد", "salla", "zid"]
WEB_KEYWORDS = ["web", "ويب", "موقع", "site", "front", "back", "full stack", "full-stack", "php", "laravel", "python", "django", "node", "react", "vue", "api", "sql", "server", "سيرفر", "استضافة", "رفع", "deploy", "javascript", "js", "html", "css","لوحة تحكم","dashboard","next.js","next","nextjs"]
CREATIVE_KEYWORDS = ["تصميم", "design", "جرافيك", "graphic", "شعار", "logo", "مونتاج", "montage", "edit", "video", "فيديو", "موشن", "فوتوشوب", "photoshop", "premiere", "بريمير", "ريلز", "reels"]
QURAN_KEYWORDS = ["قرآن","قران","قرءان", "quran", "تلاوة", "recitation", "مصحف", "تجويد", "آية","اية","ايه", "آيات", "سورة", "ديني", "دعوي", "إسلامي", "islamic"]

def send_telegram_message(title, link, source, category):
    if not BOT_TOKEN or not CHAT_ID:
        print("❌ Error: BOT_TOKEN or CHAT_ID is missing from Environment Variables!")
        return
    
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    msg = f"🔔 **طلب {category} جديد ({source})**\n\n📝 {title}\n\n🔗 {link}"
    payload = {"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"}
    try:
        requests.post(url, data=payload)
    except Exception as e:
        print(f"Error sending Telegram: {e}")

def check_project_filter(title):
    full_text = title.lower()
    if any(w in full_text for w in EXCLUDED_KEYWORDS): return None
    if any(w in full_text for w in WEB_KEYWORDS): return "ويب 💻"
    is_creative = any(w in full_text for w in CREATIVE_KEYWORDS)
    is_quran = any(w in full_text for w in QURAN_KEYWORDS)
    if is_creative and is_quran: return "قرآن 🕌"
    return None

def scrape_site(source_name, url, is_first_run=False):
    print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Scraping {source_name}...")
    try:
        response = scraper.get(url, timeout=30)
        if response.status_code != 200: return
        soup = BeautifulSoup(response.content, 'html.parser')
        projects = []

        if source_name == "Mostaql":
            rows = soup.select('tr.project-row')
            for row in rows:
                title_elem = row.select_one('h2.mrg--bt-reset a')
                if title_elem:
                    link = title_elem['href']
                    full_link = "https://mostaql.com" + link if not link.startswith("http") else link
                    projects.append((title_elem.text.strip(), full_link))
        
        elif source_name == "Khamsat":
            all_links = soup.find_all('a', href=True)
            for t in all_links:
                href = t['href']
                if "/community/requests/" in href and any(char.isdigit() for char in href):
                    title = t.text.strip()
                    if len(title) < 5: continue
                    full_link = "https://khamsat.com" + href if not href.startswith("http") else href
                    if not any(p[1] == full_link for p in projects):
                        projects.append((title, full_link))

        for title, link in projects:
            if link in processed_projects: continue
            if is_first_run:
                processed_projects.add(link)
                continue
            category = check_project_filter(title)
            if category:
                send_telegram_message(title, link, source_name, category)
                print(f"  ✅ Match Found: {title}")
            processed_projects.add(link)
    except Exception as e:
        print(f"  ❌ Error: {e}")

def main():
    print("--- Freelance Bot (Coolify Edition) Started ---")
    if not BOT_TOKEN or not CHAT_ID:
        print("🛑 Critical Error: Variables BOT_TOKEN or CHAT_ID not set!")
        return

    for source, url in URLS.items():
        scrape_site(source, url, is_first_run=True)
        time.sleep(2)
    
    print(f"Initialization Done. Tracking {len(processed_projects)} items.\n")
    while True:
        for source, url in URLS.items():
            scrape_site(source, url, is_first_run=False)
            time.sleep(3)
        time.sleep(POLL_INTERVAL)

if __name__ == "__main__":
    main()