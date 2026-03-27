import os
import time
import requests
from bs4 import BeautifulSoup
import telebot
from pdf2image import convert_from_path
import pytesseract

# --- إعداداتك ---
TOKEN = '8426413584:AAE2NSUD1fgNMO-d6Yuhk-v39IoT78ZzwT8'
CHAT_ID = '7240947590'
bot = telebot.TeleBot(TOKEN)

def get_latest_url():
    url = "https://www.joradp.dz/HAR/Index.htm"
    try:
        r = requests.get(url, timeout=20, verify=False)
        r.encoding = 'windows-1256'
        soup = BeautifulSoup(r.text, 'html.parser')
        for link in soup.find_all('a', href=True):
            if 'jo-arabe' in link['href'] and link['href'].endswith('.pdf'):
                return "https://www.joradp.dz" + link['href'].replace('../', '/')
    except: pass
    return None

last_published_url = ""

while True:
    try:
        current_url = get_latest_url()
        if current_url and current_url != last_published_url:
            print(f"🆕 وجدنا عدداً جديداً: {current_url}")
            
            # تحميل ومعالجة الصفحة الأولى
            r = requests.get(current_url, verify=False)
            with open("temp.pdf", "wb") as f: f.write(r.content)
            
            images = convert_from_path("temp.pdf", first_page=1, last_page=1)
            images[0].save("thumb.jpg")
            
            # استخراج العناوين (اختياري)
            text = pytesseract.image_to_string(images[0], lang='ara')
            summary = "\n• ".join([l.strip() for l in text.split('\n') if len(l.strip()) > 30][:5])

            caption = f"📰 **صدور عدد جديد من الجريدة الرسمية**\n\n🔹 **أهم العناوين:**\n• {summary}\n\n🔗 {current_url}"
            
            with open("thumb.jpg", "rb") as photo:
                bot.send_photo(CHAT_ID, photo, caption=caption, parse_mode='Markdown')
            
            last_published_url = current_url
            print("✅ تم النشر بنجاح!")
            
    except Exception as e:
        print(f"❌ خطأ: {e}")
    
    # انتظر ساعة قبل الفحص القادم
    time.sleep(3600)
