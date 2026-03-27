import os, time, requests, telebot, urllib3, pytesseract
from bs4 import BeautifulSoup
from pdf2image import convert_from_path

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- إعدادات البوت ---
TOKEN = '8426413584:AAE2NSUD1fgNMO-d6Yuhk-v39IoT78ZzwT8'
CHAT_ID = '7240947590' 
bot = telebot.TeleBot(TOKEN)

# "رأس المتصفح" لإقناع السيرفر أننا لسنا بوتاً
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

def get_latest_from_archive():
    # الرابط الأصلي للأرشيف
    archive_url = "https://www.joradp.dz/FTP/jo-arabe/2026/"
    print(f"🔎 محاولة اختراق الحظر وفحص الأرشيف...")
    try:
        # نرسل الطلب مع Headers لنتجاوز الخطأ 403
        r = requests.get(archive_url, headers=HEADERS, timeout=30, verify=False)
        
        if r.status_code == 403:
            print("❌ لا يزال السيرفر يرفض الدخول (403). سأجرب طريقة بديلة...")
            return None
            
        soup = BeautifulSoup(r.text, 'html.parser')
        pdf_files = [link['href'] for link in soup.find_all('a', href=True) if link['href'].startswith('A')]
        
        if pdf_files:
            pdf_files.sort(reverse=True)
            return f"{archive_url}{pdf_files[0]}"
    except Exception as e:
        print(f"❌ خطأ غير متوقع: {e}")
    return None

last_published_url = "FORCE_ACTION_NOW"

while True:
    print("\n--- محاولة فحص جديدة ---")
    current_url = get_latest_from_archive()
    
    if current_url:
        if current_url != last_published_url:
            try:
                print(f"📡 نجحنا! جاري تحميل: {current_url}")
                res = requests.get(current_url, headers=HEADERS, verify=False)
                with open("latest.pdf", "wb") as f: f.write(res.content)
                
                images = convert_from_path("latest.pdf", first_page=1, last_page=1)
                images[0].save("cover.jpg")
                
                caption = f"🚨 **جديد الجريدة الرسمية**\n\n📥 الرابط المباشر:\n{current_url}"
                with open("cover.jpg", "rb") as photo:
                    bot.send_photo(CHAT_ID, photo, caption=caption, parse_mode='Markdown')
                
                print("✅ تم الإرسال بنجاح!")
                last_published_url = current_url
            except Exception as e:
                print(f"⚠️ خطأ أثناء المعالجة: {e}")
    else:
        print("😴 السيرفر مغلق حالياً أو محظور. سأحاول مجدداً بعد قليل...")

    time.sleep(600) # فحص كل 10 دقائق
