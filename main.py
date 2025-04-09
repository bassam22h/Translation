import os
import logging
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
from googletrans import Translator, LANGUAGES

# إعدادات التسجيل
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

# إعدادات Webhook
WEBHOOK_URL = os.getenv('WEBHOOK_URL')
PORT = int(os.environ.get('PORT', 5000))

# لغات شائعة مع إيموجيات
COMMON_LANGUAGES = {
    "🇸🇦 العربية": "ar",
    "🇬🇧 English": "en",
    "🇪🇸 Español": "es",
    "🇫🇷 Français": "fr",
    "🇩🇪 Deutsch": "de",
    "🇮🇷 فارسی": "fa",
    "🇨🇳 中文": "zh-cn",
    "🇯🇵 日本語": "ja",
    "🇷🇺 Русский": "ru",
    "🇵🇹 Português": "pt",
    "🇮🇹 Italiano": "it"
}

def create_main_keyboard():
    buttons = [
        [KeyboardButton("🌐 تغيير لغة الهدف")],
        [KeyboardButton("ℹ️ المساعدة")]
    ]
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True)

def create_lang_keyboard():
    lang_keys = list(COMMON_LANGUAGES.keys())
    buttons = []
    for i in range(0, len(lang_keys), 2):
        if i+1 < len(lang_keys):
            buttons.append([lang_keys[i], lang_keys[i+1]])
        else:
            buttons.append([lang_keys[i]])
    buttons.append(["↩️ العودة للرئيسية"])
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True)

def start(update: Update, context: CallbackContext):
    # تعيين العربية كلغة افتراضية
    if 'target_lang' not in context.user_data:
        context.user_data['target_lang'] = 'ar'
        context.user_data['target_lang_name'] = '🇸🇦 العربية'
    
    welcome_msg = f"""
✨ مرحباً بك في بوت الترجمة الذكي! ✨

🔹 لغة الهدف الحالية: {context.user_data.get('target_lang_name', '🇸🇦 العربية')}
🔹 طريقة الاستخدام:
فقط أرسل النص وسأترجمه تلقائياً إلى اللغة {context.user_data.get('target_lang_name', '🇸🇦 العربية')}
مهما كانت لغة النص سيتم ترجمته إلى {context.user_data.get('target_lang_name', '🇸🇦 العربية')} مباشرة
"""
    update.message.reply_text(
        welcome_msg,
        reply_markup=create_main_keyboard()
    )

def handle_text(update: Update, context: CallbackContext):
    user_message = update.message.text
    
    # معالجة زر المساعدة
    if user_message == "ℹ️ المساعدة":
        return help_command(update, context)
        
    # تجاهل الأزرار الأخرى
    if user_message in ["🌐 تغيير لغة الهدف", "↩️ العودة للرئيسية"]:
        return
    
    if 'target_lang' not in context.user_data:
        context.user_data['target_lang'] = 'ar'
        context.user_data['target_lang_name'] = '🇸🇦 العربية'
    
    try:
        # الكشف عن لغة النص
        detected = translator.detect(user_message)
        src_lang = detected.lang
        src_lang_name = LANGUAGES.get(src_lang, src_lang)
        
        # الترجمة إلى لغة الهدف
        translation = translator.translate(
            user_message,
            dest=context.user_data['target_lang']
        )
        
        update.message.reply_text(
            f"🌐 تمت الترجمة من {src_lang_name} إلى {context.user_data['target_lang_name']}:\n\n"
            f"{translation.text}",
            reply_markup=create_main_keyboard()
        )
    
    except Exception as e:
        logger.error(f"Error in translation: {e}")
        update.message.reply_text(
            "⚠️ حدث خطأ أثناء الترجمة. يرجى المحاولة مرة أخرى.",
            reply_markup=create_main_keyboard()
        )

def set_language(update: Update, context: CallbackContext):
    update.message.reply_text(
        "📌 الرجاء اختيار لغة الهدف:",
        reply_markup=create_lang_keyboard()
    )

def handle_language_selection(update: Update, context: CallbackContext):
    user_choice = update.message.text
    
    if user_choice == "↩️ العودة للرئيسية":
        update.message.reply_text(
            "تم العودة للقائمة الرئيسية",
            reply_markup=create_main_keyboard()
        )
        return
    
    if user_choice in COMMON_LANGUAGES:
        context.user_data['target_lang'] = COMMON_LANGUAGES[user_choice]
        context.user_data['target_lang_name'] = user_choice
        update.message.reply_text(
            f"✅ تم تعيين لغة الهدف إلى: {user_choice}\n"
            "يمكنك الآن إرسال أي نص وسيتم ترجمته تلقائياً",
            reply_markup=create_main_keyboard()
        )
    else:
        update.message.reply_text(
            "⚠️ الرجاء الاختيار من القائمة",
            reply_markup=create_lang_keyboard()
        )

def help_command(update: Update, context: CallbackContext):
    help_msg = f"""
🆘 مساعدة بوت الترجمة

🔹 لغة الهدف الحالية: {context.user_data.get('target_lang_name', '🇸🇦 العربية')}
🔹 طريقة الاستخدام:
1. أرسل أي نص بأي لغة كانت وسيتم ترجمته تلقائياً

2. لتغيير لغة الهدف:
   - اضغط على زر "🌐 تغيير لغة الهدف"
   - اختر اللغة الجديدة من القائمة

📌 ملاحظة مهمة:
إذا توقف البوت عن الاستجابة، ما عليك سوى الانتظار قليلاً وسيتم معالجة طلبك تلقائياً.
الرجاء عدم تكرار إرسال الطلبات لتجنب التحميل الزائد على النظام.
"""
    update.message.reply_text(
        help_msg,
        reply_markup=create_main_keyboard()
    )

def error_handler(update: Update, context: CallbackContext):
    logger.error("Exception occurred:", exc_info=context.error)
    if update.message:
        update.message.reply_text(
            "⚠️ حدث خطأ غير متوقع. يرجى الانتظار وسيتم معالجة طلبك تلقائياً.",
            reply_markup=create_main_keyboard()
        )

def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher
    
    # معالجة الأوامر
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", help_command))
    dp.add_handler(CommandHandler("setlang", set_language))
    
    # معالجة اختيار اللغة
    dp.add_handler(MessageHandler(
        Filters.regex(r'^(🇸🇦 العربية|🇬🇧 English|🇪🇸 Español|🇫🇷 Français|🇩🇪 Deutsch|🇮🇷 فارسی|🇨🇳 中文|🇯🇵 日本語|🇷🇺 Русский|🇵🇹 Português|🇮🇹 Italiano|🌐 تغيير لغة الهدف|↩️ العودة للرئيسية)$'),
        handle_language_selection
    ))
    
    # معالجة الرسائل النصية العادية
    dp.add_handler(MessageHandler(
        Filters.text & ~Filters.command,
        handle_text
    ))
    
    dp.add_error_handler(error_handler)

    # تشغيل البوت
    if WEBHOOK_URL:
        updater.start_webhook(
            listen="0.0.0.0",
            port=PORT,
            url_path=TOKEN,
            webhook_url=f"{WEBHOOK_URL}/{TOKEN}"
        )
        logger.info(f"Bot running in webhook mode on port {PORT}")
    else:
        updater.start_polling()
        logger.info("Bot running in polling mode")

    updater.idle()

if __name__ == '__main__':
    main()
