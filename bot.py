from telegram import Update
from telegram.ext import Application, MessageHandler, CommandHandler, CallbackContext, filters
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
    mega = Mega()
    m = mega.login()  # تسجيل الدخول
    
    # التحقق إذا كان الرابط ملف أو مجلد
    file_or_folder = m.get_file(url) if '.mega.nz' in url else m.get_folder(url)
    
    downloaded_files = []
    
    if file_or_folder:
        if isinstance(file_or_folder, list):  # إذا كان الرابط يشير إلى مجلد
            for file in file_or_folder:
                downloaded_files.append(m.download(file, dest_path='./downloads'))
        elif isinstance(file_or_folder, dict):  # إذا كان الرابط يشير إلى ملف واحد
            downloaded_files.append(m.download(file_or_folder, dest_path='./downloads'))
    
    return downloaded_files

# دالة لمعالجة الرسائل في المجموعة
async def handle_message(update: Update, context: CallbackContext):
    if update.message.from_user.id != DEV_USER_ID:
        return  # لا استجابة إذا لم يكن المرسل هو المطور

    if is_mega_link(update.message.text):
        url = update.message.text.strip()

        try:
            downloaded_files = download_mega_content(url)
            for file_path in downloaded_files:
                with open(file_path, 'rb') as file:
                    await context.bot.send_document(chat_id=CHAT_ID, document=file)
            await update.message.reply_text(f"تم إرسال الملفات بنجاح!")

            # تنظيف الملفات المحملة بعد إرسالها
            for file_path in downloaded_files:
                os.remove(file_path)
        except Exception as e:
            await update.message.reply_text(f"حدث خطأ: {str(e)}")
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
