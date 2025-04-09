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

# لغات شائعة مع إيموجيات (تمت إضافة الفارسية)
COMMON_LANGUAGES = {
    "🇸🇦 العربية": "ar",
    "🇬🇧 English": "en",
    "🇪🇸 Español": "es",
    "🇫🇷 Français": "fr",
    "🇩🇪 Deutsch": "de",
    "🇮🇷 فارسی": "fa",  # أضفنا الفارسية هنا
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
    buttons = [list(COMMON_LANGUAGES.keys())[i:i+2] for i in range(0, len(COMMON_LANGUAGES), 2]
    buttons.append(["↩️ العودة للرئيسية"])
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True)

def start(update: Update, context: CallbackContext):
    # تعيين الإنجليزية كلغة افتراضية
    if 'target_lang' not in context.user_data:
        context.user_data['target_lang'] = 'en'
        context.user_data['target_lang_name'] = 'English'
    
    welcome_msg = f"""
✨ *مرحباً بك في بوت الترجمة الذكي!* ✨

🔹 *لغة الهدف الحالية:* {context.user_data.get('target_lang_name', 'English')}
🔹 *طريقة الاستخدام:*
1. فقط أرسل النص وسأترجمه تلقائياً
2. للترجمة العكسية (إلى الإنجليزية) استخدم /reverse
3. لتغيير لغة الهدف استخدم /setlang أو الزر المخصص

📌 *مثال:*
أرسل: "مرحبا كيف حالك؟"
سيتم ترجمته إلى {context.user_data.get('target_lang_name', 'English')} تلقائياً
"""
    update.message.reply_text(
        welcome_msg,
        parse_mode='Markdown',
        reply_markup=create_main_keyboard()
    )

def handle_text(update: Update, context: CallbackContext):
    user_message = update.message.text
    
    # تجاهل الأزرار
    if user_message in ["🌐 تغيير لغة الهدف", "ℹ️ المساعدة", "↩️ العودة للرئيسية"]:
        return
    
    # إذا لم يتم تعيين لغة الهدف، نستخدم الإنجليزية
    if 'target_lang' not in context.user_data:
        context.user_data['target_lang'] = 'en'
        context.user_data['target_lang_name'] = 'English'
    
    try:
        # الكشف عن لغة النص
        detected = translator.detect(user_message)
        src_lang = detected.lang
        confidence = detected.confidence * 100 if detected.confidence else 0
        
        # إذا كانت لغة النص هي لغة الهدف، نترجم للإنجليزية
        if src_lang == context.user_data['target_lang']:
            translation = translator.translate(user_message, dest='en')
            src_lang_name = LANGUAGES.get(src_lang, src_lang)
            update.message.reply_text(
                f"🔁 *تمت الترجمة العكسية إلى الإنجليزية:*\n\n"
                f"{translation.text}\n\n"
                f"لغة النص الأصلية: {src_lang_name}",
                parse_mode='Markdown',
                reply_markup=create_main_keyboard()
            )
        else:
            # الترجمة إلى لغة الهدف
            translation = translator.translate(
                user_message,
                dest=context.user_data['target_lang']
            )
            src_lang_name = LANGUAGES.get(src_lang, src_lang)
            update.message.reply_text(
                f"🌐 *تمت الترجمة من {src_lang_name} إلى {context.user_data['target_lang_name']}:*\n\n"
                f"{translation.text}",
                parse_mode='Markdown',
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

def reverse_translation(update: Update, context: CallbackContext):
    if not update.message.reply_to_message or not update.message.reply_to_message.text:
        update.message.reply_text(
            "ℹ️ لاستخدام الترجمة العكسية، يرجى الرد على الرسالة التي تريد ترجمتها إلى الإنجليزية",
            reply_markup=create_main_keyboard()
        )
        return
    
    try:
        text_to_translate = update.message.reply_to_message.text
        translation = translator.translate(text_to_translate, dest='en')
        update.message.reply_text(
            f"🔁 *الترجمة إلى الإنجليزية:*\n\n{translation.text}",
            parse_mode='Markdown',
            reply_markup=create_main_keyboard()
        )
    except Exception as e:
        logger.error(f"Error in reverse translation: {e}")
        update.message.reply_text(
            "⚠️ حدث خطأ أثناء الترجمة العكسية",
            reply_markup=create_main_keyboard()
        )

def help_command(update: Update, context: CallbackContext):
    help_msg = f"""
🆘 *مساعدة بوت الترجمة*

🔹 *لغة الهدف الحالية:* {context.user_data.get('target_lang_name', 'English')}
🔹 *الأوامر المتاحة:*
/start - بدء البوت
/setlang - تغيير لغة الهدف
/reverse - ترجمة رسالة إلى الإنجليزية (بالرد على الرسالة)
/help - عرض هذه الرسالة

📌 *طريقة الاستخدام:*
1. سيتم ترجمة أي نص ترسله تلقائياً إلى {context.user_data.get('target_lang_name', 'English')}
2. للترجمة العكسية إلى الإنجليزية، اضغط على الرسالة واختر /reverse
3. لتغيير لغة الهدف استخدم /setlang
"""
    update.message.reply_text(
        help_msg,
        parse_mode='Markdown',
        reply_markup=create_main_keyboard()
    )

def error_handler(update: Update, context: CallbackContext):
    logger.error("Exception occurred:", exc_info=context.error)
    if update.message:
        update.message.reply_text(
            "⚠️ حدث خطأ غير متوقع. يرجى المحاولة مرة أخرى.",
            reply_markup=create_main_keyboard()
        )

def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher
    
    # معالجة الأوامر
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("setlang", set_language))
    dp.add_handler(CommandHandler("reverse", reverse_translation))
    dp.add_handler(CommandHandler("help", help_command))
    
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
