import os, time, requests, telebot, urllib3, pytesseract
from bs4 import BeautifulSoup
from pdf2image import convert_from_path

# تعطيل تحذيرات الأمان
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- الإعدادات ---
TOKEN = '8426413584:AAE2NSUD1fgNMO-d6Yuhk-v39IoT78ZzwT8'
CHAT_ID = '7240947590' 
bot = telebot.TeleBot(TOKEN)

# "رأس المتصفح" لإقناع السيرفر أننا متصفح حقيقي ونتجنب الخطأ 403
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
    'Accept-Language': 'ar,en-US;q=0.7,en;q=0.3',
}

def get_latest_from_archive():
    archive_url = "https://www.joradp.dz/FTP/jo-arabe/2026/"
    print(f"🔎 محاولة الوصول للأرشيف بهوية متصفح...")
    try:
        # نرسل الطلب مع الـ Headers الجديدة
        session = requests.Session()
        r = session.get(archive_url, headers=HEADERS, timeout=30, verify=False)
        
        if r.status_code != 200:
            print(f"⚠️ فشل الدخول: كود الاستجابة {r.status_code}")
            return None
            
        soup = BeautifulSoup(r.text, 'html.parser')
        # البحث عن الملفات التي تبدأ بـ A
        pdf_files = [link['href'] for link in soup.find_all('a', href=True) if link['href'].startswith('A')]
        
        if pdf_files:
            pdf_files.sort(reverse=True)
            return f"{archive_url}{pdf_files[0]}"
    except Exception as e:
        print(f"❌ خطأ اتصال: {e}")
    return None

# قيمة البداية لإجبار البوت على النشر الآن
last_published_url = "FORCE_START_2026"

print("🚀 انطلاق البوت بنظام تخطي الحظر...")

while True:
    print("\n--- دورة فحص جديدة ---")
    current_url = get_latest_from_archive()
    
    if current_url and current_url != last_published_url:
        try:
            print(f"📡 وجدنا العدد! جاري التحميل: {current_url}")
            # التحميل أيضاً يحتاج Headers
            res = requests.get(current_url, headers=HEADERS, verify=False, timeout=60)
            
            with open("latest.pdf", "wb") as f:
                f.write(res.content)
            
            print("📥 تم التحميل. جاري معالجة الصورة والعناوين...")
            
            # معالجة الـ PDF
            images = convert_from_path("latest.pdf", first_page=1, last_page=1, dpi=150)
            images[0].save("cover.jpg", "JPEG")
            
            # قراءة النص بالعربية
            text = pytesseract.image_to_string(images[0], lang='ara')
            clean_lines = [l.strip() for l in text.split('\n') if len(l.strip()) > 35]
            summary = "\n• " + "\n• ".join(clean_lines[:5]) if clean_lines else "لا توجد عناوين واضحة."

            caption = (
                f"🚨 **جديد الجريدة الرسمية الجزائرية**\n\n"
                f"🔹 **من أهم العناوين:**\n{summary}\n\n"
                f"📥 **رابط PDF المباشر:**\n{current_url}"
            )

            with open("cover.jpg", "rb") as photo:
                bot.send_photo(CHAT_ID, photo, caption=caption, parse_mode='Markdown')
            
            print("✅ تم النشر في القناة بنجاح!")
            last_published_url = current_url
            
        except Exception as e:
            print(f"⚠️ خطأ أثناء المعالجة: {e}")
    else:
        if not current_url:
            print("❌ لا تزال مشكلة الـ 403 قائمة، سأحاول مجدداً بعد 10 دقائق.")
        else:
            print("💤 لا يوجد تحديث جديد في الأرشيف.")

    time.sleep(600) # فحص كل 10 دقائق
