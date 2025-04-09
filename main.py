import os
import logging
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
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

# لغات شائعة للعرض في لوحة المفاتيح
COMMON_LANGUAGES = {
    'العربية': 'ar',
    'English': 'en',
    'Español': 'es',
    'Français': 'fr',
    'Deutsch': 'de',
    '中文': 'zh-cn',
    '日本語': 'ja',
    'Русский': 'ru',
    'Português': 'pt',
    'Italiano': 'it'
}

# إنشاء لوحة مفاتيح للغات
def get_language_keyboard():
    buttons = [[KeyboardButton(lang)] for lang in COMMON_LANGUAGES.keys()]
    buttons.append([KeyboardButton("إلغاء")])
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True)

def start(update: Update, context: CallbackContext):
    welcome_msg = """
🌟 *مرحباً بك في بوت الترجمة الذكي!* 🌟

🚀 *كيفية الاستخدام:*
1. أرسل لي النص الذي تريد ترجمته (أي لغة)
2. سأقوم باكتشاف اللغة تلقائياً
3. اختر اللغة التي تريد الترجمة إليها

💡 *مثال:*
أرسل: "Hello my friend"
ثم اختر: "العربية" لترجمة النص للعربية

✅ *اللغات المدعومة:* جميع اللغات الرئيسية
    """
    
    update.message.reply_text(
        welcome_msg,
        parse_mode='Markdown',
        reply_markup=ReplyKeyboardMarkup([['إلغاء']], resize_keyboard=True)
    )

def handle_text(update: Update, context: CallbackContext):
    user_message = update.message.text
    
    if user_message == "إلغاء":
        update.message.reply_text(
            "تم إلغاء العملية الحالية. يمكنك إرسال نص جديد للترجمة.",
            reply_markup=ReplyKeyboardMarkup([['إلغاء']], resize_keyboard=True)
        )
        context.user_data.clear()
        return
    
    try:
        # الكشف عن لغة النص
        detected = translator.detect(user_message)
        src_lang = detected.lang
        confidence = detected.confidence * 100 if detected.confidence else 0
        
        # حفظ النص ولغة المصدر
        context.user_data['text_to_translate'] = user_message
        context.user_data['src_lang'] = src_lang
        
        # إعداد رسالة الرد
        lang_name = LANGUAGES.get(src_lang, src_lang)
        confidence_msg = f" (ثقة: {confidence:.1f}%)" if confidence > 0 else ""
        
        update.message.reply_text(
            f"🔍 *تم الكشف عن اللغة:* {lang_name}{confidence_msg}\n\n"
            "الآن اختر *اللغة الهدف* للترجمة من القائمة أدناه، "
            "أو اكتب اسم اللغة بالإنجليزية (مثل 'french' أو 'german')",
            parse_mode='Markdown',
            reply_markup=get_language_keyboard()
        )
    
    except Exception as e:
        logger.error(f"Error in language detection: {e}", exc_info=True)
        update.message.reply_text(
            "⚠️ عذراً، لم أتمكن من تحديد لغة النص. يرجى المحاولة مرة أخرى.",
            reply_markup=ReplyKeyboardMarkup([['إلغاء']], resize_keyboard=True)
        )

def handle_language_selection(update: Update, context: CallbackContext):
    user_message = update.message.text
    
    if user_message == "إلغاء":
        update.message.reply_text(
            "تم إلغاء العملية الحالية. يمكنك إرسال نص جديد للترجمة.",
            reply_markup=ReplyKeyboardMarkup([['إلغاء']], resize_keyboard=True)
        )
        context.user_data.clear()
        return
    
    try:
        # الحصول على النص المحفوظ
        if 'text_to_translate' not in context.user_data:
            update.message.reply_text(
                "⚠️ لم يتم العثور على نص للترجمة. يرجى إرسال النص أولاً.",
                reply_markup=ReplyKeyboardMarkup([['إلغاء']], resize_keyboard=True)
            )
            return
        
        text_to_translate = context.user_data['text_to_translate']
        src_lang = context.user_data.get('src_lang', 'auto')
        
        # تحديد لغة الهدف
        dest_lang = COMMON_LANGUAGES.get(user_message)
        
        if not dest_lang:
            # إذا كانت اللغة غير موجودة في القائمة، نبحث في جميع اللغات
            dest_lang = None
            for code, name in LANGUAGES.items():
                if user_message.lower() in name.lower():
                    dest_lang = code
                    break
            
            if not dest_lang:
                update.message.reply_text(
                    "⚠️ لم يتم التعرف على اللغة المطلوبة. يرجى اختيار لغة من القائمة أو كتابة اسم اللغة بشكل صحيح.",
                    reply_markup=get_language_keyboard()
                )
                return
        
        # تنفيذ الترجمة
        translation = translator.translate(
            text_to_translate,
            src=src_lang,
            dest=dest_lang
        )
        
        # إعداد رسالة النتيجة
        src_lang_name = LANGUAGES.get(src_lang, src_lang)
        dest_lang_name = LANGUAGES.get(dest_lang, dest_lang)
        
        update.message.reply_text(
            f"🌍 *الترجمة من {src_lang_name} إلى {dest_lang_name}:*\n\n"
            f"{translation.text}\n\n"
            "يمكنك إرسال نص جديد للترجمة أو استخدام /help لرؤية التعليمات.",
            parse_mode='Markdown',
            reply_markup=ReplyKeyboardMarkup([['إلغاء']], resize_keyboard=True)
        )
        
        # مسح البيانات المؤقتة
        context.user_data.clear()
    
    except Exception as e:
        logger.error(f"Error in translation: {e}", exc_info=True)
        update.message.reply_text(
            "⚠️ حدث خطأ أثناء الترجمة. يرجى المحاولة مرة أخرى.",
            reply_markup=get_language_keyboard()
        )

def help_command(update: Update, context: CallbackContext):
    help_msg = """
🆘 *مساعدة بوت الترجمة*

📝 *طريقة الاستخدام:*
1. أرسل النص الذي تريد ترجمته (أي لغة)
2. سأكتشف اللغة تلقائياً
3. اختر اللغة الهدف من القائمة أو اكتب اسمها

🎯 *مثال:*
أرسل: "Bonjour comment ça va؟"
ثم اختر: "English" لترجمة النص للإنجليزية

🌐 *اللغات المدعومة:* جميع اللغات الرئيسية
استخدم أسماء اللغات بالإنجليزية مثل:
- french, german, spanish, russian, etc.

❌ *لإلغاء أي عملية:* اكتب أو اضغط على "إلغاء"
    """
    
    update.message.reply_text(
        help_msg,
        parse_mode='Markdown',
        reply_markup=ReplyKeyboardMarkup([['إلغاء']], resize_keyboard=True)
    )

def error_handler(update: Update, context: CallbackContext):
    logger.error(msg="Exception while handling an update:", exc_info=context.error)
    if update and update.message:
        update.message.reply_text(
            "⚠️ حدث خطأ غير متوقع. يرجى المحاولة مرة أخرى.",
            reply_markup=ReplyKeyboardMarkup([['إلغاء']], resize_keyboard=True)
        )

def main():
    updater = Updater(TOKEN, use_context=True)
    
    dp = updater.dispatcher
    
    # معالجة الأوامر
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", help_command))
    
    # معالجة النص العادي (المرحلة الأولى: إرسال النص)
    dp.add_handler(MessageHandler(
        Filters.text & ~Filters.command & ~Filters.regex(r'^(إلغاء)$'),
        handle_text
    ))
    
    # معالجة اختيار اللغة (المرحلة الثانية)
    dp.add_handler(MessageHandler(
        Filters.regex(r'^(إلغاء|العربية|English|Español|Français|Deutsch|中文|日本語|Русский|Português|Italiano|[a-zA-Z]+)$'),
        handle_language_selection
    ))
    
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
