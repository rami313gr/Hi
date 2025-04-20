from telegram import Update
from telegram.ext import Application, MessageHandler, filters, CommandHandler, CallbackContext
from mega import Mega
import os
import re

# إعدادات البوت من المتغيرات البيئية
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')  # أو اسم المجموعة
DEV_USER_ID = int(os.getenv('DEV_USER_ID'))  # ID المطور

# دالة للتحقق إذا كانت الرسالة تحتوي على رابط ميغا
def is_mega_link(text):
    mega_link_pattern = r'(https?://(?:www\.)?mega\.nz/\S+)'
    return re.search(mega_link_pattern, text) is not None

# دالة لتحميل محتويات المجلد
def download_mega_content(url: str):
    try:
        mega = Mega()
        m = mega.login()  # تسجيل الدخول
        # محاولة الحصول على المحتويات
        content = m.get_folder(url)  # هذا لتحديد المجلد
        downloaded_files = []
        
        # التحقق من نوع المحتوى (مجلد أو ملف)
        for file in content:
            file_path = file['name']
            # تحميل الملف
            m.download(file, dest_path='./downloads')
            downloaded_files.append(file_path)
        
        return downloaded_files
    
    except Exception as e:
        return str(e)  # في حالة وجود خطأ نعيد الخطأ كرسالة

# دالة لمعالجة الرسائل في المجموعة
async def handle_message(update: Update, context: CallbackContext):
    if update.message.from_user.id != DEV_USER_ID:
        return  # لا استجابة إذا لم يكن المرسل هو المطور

    if is_mega_link(update.message.text):
        url = update.message.text.strip()

        try:
            downloaded_files = download_mega_content(url)
            if isinstance(downloaded_files, list):
                for file_path in downloaded_files:
                    with open(file_path, 'rb') as file:
                        await context.bot.send_document(chat_id=CHAT_ID, document=file)
                await update.message.reply_text(f"تم إرسال الملفات بنجاح!")
            else:
                # إذا كان هناك خطأ
                await update.message.reply_text(f"حدث خطأ: {downloaded_files}")
        except Exception as e:
            await update.message.reply_text(f"حدث خطأ أثناء المعالجة: {str(e)}")
    else:
        await update.message.reply_text("يرجى إرسال رابط ميغا صحيح.")

# دالة لمعالجة الأمر /start
async def start(update: Update, context: CallbackContext):
    await update.message.reply_text("البوت يعمل بنجاح!")

def main():
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    # إضافة معالج الرسائل في المجموعة
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # إضافة معالج للأمر /start
    application.add_handler(CommandHandler("start", start))

    # بدء البوت
    application.run_polling()

if __name__ == '__main__':
    main()
