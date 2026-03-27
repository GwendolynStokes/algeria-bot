import os, time, requests, telebot, urllib3, pytesseract
from bs4 import BeautifulSoup
from pdf2image import convert_from_path

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- إعداداتك ---
TOKEN = '8426413584:AAE2NSUD1fgNMO-d6Yuhk-v39IoT78ZzwT8'
CHAT_ID = '7240947590' 
bot = telebot.TeleBot(TOKEN)

def get_latest_from_archive():
    archive_url = "https://www.joradp.dz/FTP/jo-arabe/2026/"
    print(f"🔎 جاري فحص الأرشيف الآن: {archive_url}")
    try:
        r = requests.get(archive_url, timeout=30, verify=False)
        soup = BeautifulSoup(r.text, 'html.parser')
        pdf_files = [link['href'] for link in soup.find_all('a', href=True) if link['href'].startswith('A')]
        if pdf_files:
            pdf_files.sort(reverse=True)
            return f"{archive_url}{pdf_files[0]}"
    except Exception as e:
        print(f"❌ خطأ اتصال بالأرشيف: {e}")
    return None

last_published_url = "test_force" # وضعناها هكذا ليجبره على الإرسال فوراً

while True:
    print("🔄 بدأت دورة فحص جديدة...")
    current_url = get_latest_from_archive()
    
    if current_url and current_url != last_published_url:
        try:
            print(f"📡 وجدنا ملفاً: {current_url} .. جاري التحميل...")
            res = requests.get(current_url, verify=False)
            with open("latest.pdf", "wb") as f: f.write(res.content)
            print("📥 اكتمل التحميل. جاري تحويل الصفحة لصورة (هذا قد يستغرق دقيقة)...")
            
            images = convert_from_path("latest.pdf", first_page=1, last_page=1)
            images[0].save("cover.jpg")
            print("🖼️ تم إنشاء الصورة. جاري قراءة النصوص العربية (OCR)...")
            
            text = pytesseract.image_to_string(images[0], lang='ara')
            print("📝 تمت قراءة النص بنجاح. جاري الإرسال لتلغرام...")
            
            caption = f"🚨 **جديد الجريدة الرسمية**\n\n📥 التحميل:\n{current_url}"
            with open("cover.jpg", "rb") as photo:
                bot.send_photo(CHAT_ID, photo, caption=caption, parse_mode='Markdown')
            
            print("✅ تم الإرسال بنجاح!")
            last_published_url = current_url
        except Exception as e:
            print(f"⚠️ تعثر البوت أثناء المعالجة: {e}")
    
    print("😴 سأنام لمدة 20 دقيقة قبل الفحص القادم...")
    time.sleep(1200)
