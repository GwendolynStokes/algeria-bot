import os, time, requests, telebot, urllib3, pytesseract
from bs4 import BeautifulSoup
from pdf2image import convert_from_path

# تعطيل تحذيرات الاتصال غير الآمن لسيرفر الجريدة
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- إعدادات البوت الخاصة بك ---
TOKEN = '8426413584:AAE2NSUD1fgNMO-d6Yuhk-v39IoT78ZzwT8'
CHAT_ID = '7240947590' 
bot = telebot.TeleBot(TOKEN)

def get_latest_from_archive():
    """وظيفة للبحث عن أحدث ملف PDF في أرشيف 2026 المباشر"""
    archive_url = "https://www.joradp.dz/FTP/jo-arabe/2026/"
    print(f"🔎 فحص الأرشيف المباشر الآن: {archive_url}")
    try:
        r = requests.get(archive_url, timeout=30, verify=False)
        if r.status_code != 200:
            print(f"⚠️ سيرفر الجريدة استجاب بكود: {r.status_code}")
            return None
            
        soup = BeautifulSoup(r.text, 'html.parser')
        # البحث عن الروابط التي تبدأ بـ A وتنتهي بـ .pdf
        pdf_files = [link['href'] for link in soup.find_all('a', href=True) if link['href'].startswith('A') and link['href'].lower().endswith('.pdf')]
        
        if pdf_files:
            pdf_files.sort(reverse=True) # ترتيب للحصول على أكبر رقم عدد
            latest = f"{archive_url}{pdf_files[0]}"
            print(f"✅ تم العثور على أحدث ملف في الأرشيف: {pdf_files[0]}")
            return latest
    except Exception as e:
        print(f"❌ خطأ أثناء الاتصال بالأرشيف: {e}")
    return None

# --- نقطة البداية الحاشمة ---
# ملاحظة: غيرنا هذه القيمة لنجبر البوت على إرسال العدد الأخير حالاً عند أول تشغيل
last_published_url = "RESTART_AND_SEND_NOW" 

print("🚀 تم تشغيل البوت بنجاح.. بدأ نظام المراقبة الذكي 24/7")

while True:
    print("\n--- دورة فحص جديدة ---")
    current_url = get_latest_from_archive()
    
    if current_url and current_url != last_published_url:
        try:
            print(f"📡 اكتشاف تحديث! جاري تحميل الملف: {current_url}")
            res = requests.get(current_url, verify=False, timeout=60)
            
            with open("latest.pdf", "wb") as f:
                f.write(res.content)
            print("📥 اكتمل التحميل. جاري تحويل الغلاف لصورة...")

            # تحويل الصفحة الأولى فقط
            images = convert_from_path("latest.pdf", first_page=1, last_page=1, dpi=150)
            images[0].save("cover.jpg", "JPEG")
            print("🖼️ تم تجهيز الصورة. جاري استخراج العناوين (OCR العربية)...")

            # قراءة النصوص
            raw_text = pytesseract.image_to_string(images[0], lang='ara')
            clean_lines = [line.strip() for line in raw_text.split('\n') if len(line.strip()) > 35]
            summary = "\n• " + "\n• ".join(clean_lines[:6]) if clean_lines else "لم يتم استخراج عناوين واضحة."

            # تجهيز المنشور
            caption = (
                f"🚨 **صدور عدد جديد من الجريدة الرسمية**\n\n"
                f"🔹 **أهم العناوين المستخرجة:**\n{summary}\n\n"
                f"📥 **رابط التحميل المباشر:**\n{current_url}"
            )

            print("📤 جاري الإرسال إلى تلغرام...")
            with open("cover.jpg", "rb") as photo:
                bot.send_photo(CHAT_ID, photo, caption=caption, parse_mode='Markdown')
            
            print("✨ مبروك! تم النشر بنجاح.")
            last_published_url = current_url # تخزين الرابط لمنع التكرار

        except Exception as e:
            print(f"⚠️ فشل البوت في معالجة العدد: {e}")
        finally:
            # تنظيف الملفات المؤقتة لتوفير مساحة السيرفر
            for temp_file in ["latest.pdf", "cover.jpg"]:
                if os.path.exists(temp_file): os.remove(temp_file)
    else:
        print("💤 لا يوجد عدد جديد حالياً في الأرشيف.")

    # الانتظار لمدة 20 دقيقة قبل الفحص التالي
    print("⏰ سأنام لمدة 20 دقيقة (1200 ثانية)...")
    time.sleep(1200)
