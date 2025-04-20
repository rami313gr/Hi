from telegram import Update
from telegram.ext import Updater, MessageHandler, Filters, CallbackContext
from mega import Mega
import os
import re

# إعدادات البوت من المتغيرات البيئية
import os
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
    content = m.get_url(url)  # الحصول على محتويات الرابط (مجلد أو ملف)
    
    if content['type'] == 'folder':
        files = content['files']
        downloaded_files = []
        for file in files:
            file_path = file['name']
            downloaded_files.append(m.download(file, dest_path='./downloads'))
        return downloaded_files
    elif content['type'] == 'file':
        file_path = content['name']
        m.download(content, dest_path='./downloads')
        return [file_path]
    return []

# دالة لمعالجة الرسائل في المجموعة
def handle_message(update: Update, context: CallbackContext):
    if update.message.from_user.id != DEV_USER_ID:
        return  # لا استجابة إذا لم يكن المرسل هو المطور

    if is_mega_link(update.message.text):
        url = update.message.text.strip()

        try:
            downloaded_files = download_mega_content(url)
            for file_path in downloaded_files:
                with open(file_path, 'rb') as file:
                    context.bot.send_document(chat_id=CHAT_ID, document=file)
            update.message.reply_text(f"تم إرسال الملفات بنجاح!")

            # تنظيف الملفات المحملة بعد إرسالها
            for file_path in downloaded_files:
                os.remove(file_path)
        except Exception as e:
            update.message.reply_text(f"حدث خطأ: {str(e)}")
    else:
        update.message.reply_text("يرجى إرسال رابط ميغا صحيح.")

def main():
    updater = Updater(TELEGRAM_TOKEN)
    dp = updater.dispatcher

    # إضافة معالج الرسائل في المجموعة
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))

    # بدء البوت
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
