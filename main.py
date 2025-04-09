import os
import logging
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
from googletrans import Translator, LANGUAGES

# إعدادات التسجيل للتصحيح
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# تهيئة المترجم
translator = Translator()

# الحصول على التوكن من متغيرات البيئة
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
if not TOKEN:
    raise ValueError("لم يتم تعيين TELEGRAM_BOT_TOKEN في متغيرات البيئة")

# الحصول على إعدادات Webhook
WEBHOOK_URL = os.getenv('WEBHOOK_URL')  # مثال: https://your-bot-name.onrender.com
PORT = int(os.environ.get('PORT', 5000))  # Render يستخدم PORT تلقائياً

# لوحة المفاتيح للغات الشائعة
language_keyboard = [
    ['العربية', 'English', 'Español'],
    ['Français', '中文', 'Русский'],
    ['كشف اللغة تلقائياً']
]
reply_markup = ReplyKeyboardMarkup(language_keyboard, resize_keyboard=True)

def translate_message(update: Update, context: CallbackContext):
    user_message = update.message.text
    
    if user_message in ['العربية', 'English', 'Español', 'Français', '中文', 'Русский']:
        context.user_data['target_lang'] = {
            'العربية': 'ar',
            'English': 'en',
            'Español': 'es',
            'Français': 'fr',
            '中文': 'zh-cn',
            'Русский': 'ru'
        }[user_message]
        
        update.message.reply_text(
            f"تم اختيار لغة الهدف: {user_message}\n"
            "الآن أرسل النص الذي تريد ترجمته:",
            reply_markup=ReplyKeyboardMarkup([['إلغاء']], resize_keyboard=True)
        )
        return
    
    if user_message == "كشف اللغة تلقائياً":
        context.user_data['auto_detect'] = True
        update.message.reply_text(
            "تم تفعيل الكشف التلقائي للغة.\n"
            "الآن أرسل النص الذي تريد ترجمته:",
            reply_markup=ReplyKeyboardMarkup([['إلغاء']], resize_keyboard=True)
        )
        return
    
    if user_message == "إلغاء":
        update.message.reply_text(
            "تم الإلغاء. اختر لغة الهدف من جديد:",
            reply_markup=reply_markup
        )
        context.user_data.clear()
        return
    
    if 'target_lang' in context.user_data or 'auto_detect' in context.user_data:
        try:
            if context.user_data.get('auto_detect'):
                detected = translator.detect(user_message)
                src_lang = detected.lang
                confidence = detected.confidence * 100
                
                if confidence < 60:
                    update.message.reply_text(
                        f"تم الكشف عن اللغة: {LANGUAGES.get(src_lang, src_lang)} (ثقة: {confidence:.1f}%)\n"
                        "الثقة منخفضة، الرجاء تحديد اللغة يدوياً.",
                        reply_markup=reply_markup
                    )
                    return
                
                translation = translator.translate(user_message, dest='en')
                
                update.message.reply_text(
                    f"تم الكشف عن اللغة: {LANGUAGES.get(src_lang, src_lang)} (ثقة: {confidence:.1f}%)\n\n"
                    f"الترجمة إلى الإنجليزية:\n{translation.text}\n\n"
                    "اختر لغة أخرى للترجمة إذا أردت:",
                    reply_markup=reply_markup
                )
                context.user_data.clear()
            
            elif 'target_lang' in context.user_data:
                detected = translator.detect(user_message)
                src_lang = detected.lang
                
                translation = translator.translate(
                    user_message,
                    src=src_lang,
                    dest=context.user_data['target_lang']
                )
                
                update.message.reply_text(
                    f"تمت الترجمة من {LANGUAGES.get(src_lang, src_lang)} إلى {LANGUAGES.get(context.user_data['target_lang'], context.user_data['target_lang'])}:\n\n"
                    f"{translation.text}",
                    reply_markup=reply_markup
                )
                context.user_data.clear()
        
        except Exception as e:
            logger.error(f"Error in translation: {e}", exc_info=True)
            update.message.reply_text(
                "حدث خطأ أثناء الترجمة. يرجى المحاولة مرة أخرى.",
                reply_markup=reply_markup
            )
            context.user_data.clear()
    
    else:
        update.message.reply_text(
            "مرحباً! يرجى اختيار لغة الهدف أولاً:",
            reply_markup=reply_markup
        )

def start(update: Update, context: CallbackContext):
    update.message.reply_text(
        "مرحباً في بوت الترجمة الذكي!\n\n"
        "يمكنني:\n"
        "1. ترجمة النص إلى اللغة التي تختارها\n"
        "2. كشف اللغة تلقائياً وترجمة النص\n\n"
        "اختر لغة الهدف من لوحة المفاتيح أدناه:",
        reply_markup=reply_markup
    )

def help_command(update: Update, context: CallbackContext):
    update.message.reply_text(
        "كيفية استخدام البوت:\n\n"
        "1. اختر لغة الهدف من لوحة المفاتيح\n"
        "2. أرسل النص الذي تريد ترجمته\n"
        "3. أو اختر 'كشف اللغة تلقائياً' ثم أرسل النص\n\n"
        "يمكنك الضغط على 'إلغاء' في أي وقت لبدء من جديد.",
        reply_markup=reply_markup
    )

def error_handler(update: Update, context: CallbackContext):
    logger.error(msg="Exception while handling an update:", exc_info=context.error)

def main():
    updater = Updater(TOKEN, use_context=True)
    
    dp = updater.dispatcher
    
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", help_command))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, translate_message))
    
    dp.add_error_handler(error_handler)

    # تشغيل البوت حسب البيئة
    if WEBHOOK_URL:
        # وضع Webhook (للتشغيل على Render)
        updater.start_webhook(
            listen="0.0.0.0",
            port=PORT,
            url_path=TOKEN,
            webhook_url=f"{WEBHOOK_URL}/{TOKEN}"
        )
        logger.info(f"Bot running in webhook mode on port {PORT}")
    else:
        # وضع Polling (للتنمية المحلية)
        updater.start_polling()
        logger.info("Bot running in polling mode")

    updater.idle()

if __name__ == '__main__':
    main()
