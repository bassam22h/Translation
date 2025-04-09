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
    "🇨🇳 中文": "zh-cn",
    "🇯🇵 日本語": "ja",
    "🇷🇺 Русский": "ru",
    "🇵🇹 Português": "pt",
    "🇮🇹 Italiano": "it"
}

def create_keyboard():
    buttons = [[KeyboardButton(lang)] for lang in COMMON_LANGUAGES.keys()]
    buttons.append([KeyboardButton("❌ إلغاء")])
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True)

def start(update: Update, context: CallbackContext):
    welcome_msg = """
✨ *مرحباً بك في بوت الترجمة الذكي!* ✨

📝 *كيفية الاستخدام:*
1. أرسل لي النص الذي تريد ترجمته
2. اختر اللغة الهدف من القائمة
3. احصل على الترجمة فوراً!

🌍 *يدعم جميع اللغات الرئيسية*
"""
    update.message.reply_text(
        welcome_msg,
        parse_mode='Markdown',
        reply_markup=ReplyKeyboardMarkup([[KeyboardButton("❌ إلغاء")]], resize_keyboard=True)
    )

def handle_text(update: Update, context: CallbackContext):
    user_message = update.message.text
    
    if user_message == "❌ إلغاء":
        update.message.reply_text(
            "تم إلغاء العملية. يمكنك إرسال نص جديد للترجمة.",
            reply_markup=ReplyKeyboardMarkup([[KeyboardButton("❌ إلغاء")]], resize_keyboard=True)
        )
        context.user_data.clear()
        return
    
    # حفظ النص في الذاكرة المؤقتة
    context.user_data['text_to_translate'] = user_message
    
    try:
        # الكشف عن لغة النص
        detected = translator.detect(user_message)
        src_lang = detected.lang
        confidence = detected.confidence * 100 if detected.confidence else 0
        
        # إعداد رسالة الرد
        lang_name = LANGUAGES.get(src_lang, src_lang)
        confidence_msg = f" (دقة الكشف: {confidence:.1f}%)" if confidence > 0 else ""
        
        update.message.reply_text(
            f"🔍 *تم الكشف عن اللغة:* {lang_name}{confidence_msg}\n\n"
            "الرجاء اختيار *اللغة الهدف* للترجمة:",
            parse_mode='Markdown',
            reply_markup=create_keyboard()
        )
    
    except Exception as e:
        logger.error(f"Error in detection: {e}")
        update.message.reply_text(
            "⚠️ حدث خطأ في تحديد اللغة. يرجى المحاولة مرة أخرى.",
            reply_markup=ReplyKeyboardMarkup([[KeyboardButton("❌ إلغاء")]], resize_keyboard=True)
        )

def handle_language_selection(update: Update, context: CallbackContext):
    user_choice = update.message.text
    
    if user_choice == "❌ إلغاء":
        update.message.reply_text(
            "تم إلغاء العملية. يمكنك إرسال نص جديد للترجمة.",
            reply_markup=ReplyKeyboardMarkup([[KeyboardButton("❌ إلغاء")]], resize_keyboard=True)
        )
        context.user_data.clear()
        return
    
    if 'text_to_translate' not in context.user_data:
        update.message.reply_text(
            "⚠️ لم يتم العثور على نص للترجمة. يرجى إرسال النص أولاً.",
            reply_markup=ReplyKeyboardMarkup([[KeyboardButton("❌ إلغاء")]], resize_keyboard=True)
        )
        return
    
    text_to_translate = context.user_data['text_to_translate']
    
    try:
        # البحث عن اللغة المختارة
        dest_lang = COMMON_LANGUAGES.get(user_choice)
        
        if not dest_lang:
            # إذا كانت اللغة غير موجودة في القائمة، نبحث في جميع اللغات
            for name, code in LANGUAGES.items():
                if user_choice.lower() in name.lower():
                    dest_lang = code
                    break
            
            if not dest_lang:
                update.message.reply_text(
                    "⚠️ لم يتم التعرف على اللغة المطلوبة. يرجى الاختيار من القائمة:",
                    reply_markup=create_keyboard()
                )
                return
        
        # تنفيذ الترجمة
        translation = translator.translate(
            text_to_translate,
            dest=dest_lang
        )
        
        # إعداد رسالة النتيجة
        src_lang_name = LANGUAGES.get(translation.src, translation.src)
        dest_lang_name = LANGUAGES.get(dest_lang, dest_lang)
        
        update.message.reply_text(
            f"🌐 *الترجمة من {src_lang_name} إلى {dest_lang_name}:*\n\n"
            f"{translation.text}\n\n"
            "يمكنك إرسال نص جديد للترجمة أو استخدام /help للمساعدة.",
            parse_mode='Markdown',
            reply_markup=ReplyKeyboardMarkup([[KeyboardButton("❌ إلغاء")]], resize_keyboard=True)
        )
        
        # مسح البيانات المؤقتة
        context.user_data.clear()
    
    except Exception as e:
        logger.error(f"Error in translation: {e}")
        update.message.reply_text(
            "⚠️ حدث خطأ أثناء الترجمة. يرجى المحاولة مرة أخرى.",
            reply_markup=create_keyboard()
        )

def help_command(update: Update, context: CallbackContext):
    help_msg = """
🆘 *مساعدة بوت الترجمة*

📌 *طريقة الاستخدام البسيطة:*
1. أرسل النص المطلوب (أي لغة)
2. اختر اللغة الهدف من القائمة
3. احصل على الترجمة فوراً!

💡 *مثال:*
أرسل: "مرحبا كيف حالك؟"
ثم اختر: "English" لترجمة النص للإنجليزية

❌ *لإلغاء أي عملية:* اضغط على "إلغاء"
"""
    update.message.reply_text(
        help_msg,
        parse_mode='Markdown',
        reply_markup=ReplyKeyboardMarkup([[KeyboardButton("❌ إلغاء")]], resize_keyboard=True)
    )

def error_handler(update: Update, context: CallbackContext):
    logger.error("Exception occurred:", exc_info=context.error)
    if update.message:
        update.message.reply_text(
            "⚠️ حدث خطأ غير متوقع. يرجى المحاولة مرة أخرى.",
            reply_markup=ReplyKeyboardMarkup([[KeyboardButton("❌ إلغاء")]], resize_keyboard=True)
        )

def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher
    
    # معالجة الأوامر
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", help_command))
    
    # معالجة النص العادي
    dp.add_handler(MessageHandler(
        Filters.text & ~Filters.command & ~Filters.regex(r'^(❌ إلغاء|🇸🇦 العربية|🇬🇧 English|🇪🇸 Español|🇫🇷 Français|🇩🇪 Deutsch|🇨🇳 中文|🇯🇵 日本語|🇷🇺 Русский|🇵🇹 Português|🇮🇹 Italiano)$'),
        handle_text
    ))
    
    # معالجة اختيار اللغة
    dp.add_handler(MessageHandler(
        Filters.regex(r'^(❌ إلغاء|🇸🇦 العربية|🇬🇧 English|🇪🇸 Español|🇫🇷 Français|🇩🇪 Deutsch|🇨🇳 中文|🇯🇵 日本語|🇷🇺 Русский|🇵🇹 Português|🇮🇹 Italiano)$'),
        handle_language_selection
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
