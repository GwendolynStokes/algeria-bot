import os
import time
import requests
from bs4 import BeautifulSoup
import telebot
from pdf2image import convert_from_path
import pytesseract
import urllib3

# تعطيل تحذيرات الأمان لملاءمة سيرفر الجريدة
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- إعداداتك ---
TOKEN = '8426413584:AAE2NSUD1fgNMO-d6Yuhk-v39IoT78ZzwT8'
CHAT_ID = '7240947590' 
bot = telebot.TeleBot(TOKEN)

def get_latest_from_archive():
    # الرابط المباشر لأرشيف سنة 2026
    archive_url = "https://www.joradp.dz/FTP/jo-arabe/2026/"
    print(f"🔎 فحص الأرشيف المباشر: {archive_url}")
    
    try:
        r = requests.get(archive_url, timeout=25, verify=False)
        soup = BeautifulSoup(r.text, 'html.parser')
        
        # استخراج كافة ملفات PDF التي تبدأ بحرف A (الجرائد العربية)
        pdf_files = []
        for link in soup.find_all('a', href=True):
            file_name = link['href']
            if file_name.lower().endswith('.pdf') and file_name.startswith('A'):
                pdf_files.append(file_name)
        
        if pdf_files:
            # ترتيب الملفات تنازلياً للحصول على أحدث رقم عدد
            pdf_files.sort(reverse=True)
            return f"{archive_url}{pdf_files[0]}"
            
    except Exception as e:
        print(f"❌ خطأ في الاتصال بالأرشيف: {e}")
    return None

# اجعلها فارغة في أول مرة ليقوم بنشر آخر عدد موجود حالياً فوراً
last_published_url = "" 

print("🚀 البوت بدأ بمراقبة الأرشيف المباشر 24/7...")

while True:
    try:
        current_url = get_latest_from_archive()
        
        if current_url and current_url != last_published_url:
            print(f"🆕 اكتشاف عدد جديد في الأرشيف: {current_url}")
            
            # تحميل الملف للمعالجة
            response = requests.get(current_url, verify=False)
            with open("latest.pdf", "wb") as f:
                f.write(response.content)
            
            # تحويل الصفحة الأولى فقط كصورة غلاف للمنشور
            images = convert_from_path("latest.pdf", first_page=1, last_page=1, dpi=150)
            images[0].save("cover.jpg", "JPEG")
            
            # استخراج العناوين باستخدام OCR (المحرك الذي ثبته)
            raw_text = pytesseract.image_to_string(images[0], lang='ara')
            # تنظيف النص واستخراج السطور الطويلة التي غالباً ما تكون عناوين
            clean_lines = [l.strip() for l in raw_text.split('\n') if len(l.strip()) > 35]
            summary = "\n• " + "\n• ".join(clean_lines[:6]) 

            # تنسيق المنشور الاحترافي
            caption = (
                f"🚨 **جديد الجريدة الرسمية الجزائرية**\n\n"
                f"🔹 **أهم العناوين في هذا العدد:**\n{summary}\n\n"
                f"📥 **رابط التحميل المباشر (PDF):**\n{current_url}"
            )
            
            # الإرسال إلى تلغرام
            with open("cover.jpg", "rb") as photo:
                bot.send_photo(CHAT_ID, photo, caption=caption, parse_mode='Markdown')
            
            last_published_url = current_url
            print("✅ تم النشر بنجاح!")
            
            # تنظيف الملفات المؤقتة
            if os.path.exists("latest.pdf"): os.remove("latest.pdf")
            if os.path.exists("cover.jpg"): os.remove("cover.jpg")

    except Exception as e:
        print(f"⚠️ خطأ أثناء الدورة: {e}")
    
    # فحص الأرشيف كل 20 دقيقة لضمان السرعة القصوى
    time.sleep(1200)
