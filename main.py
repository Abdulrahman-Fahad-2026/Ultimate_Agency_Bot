import os
import time
import sqlite3
from dotenv import load_dotenv
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    ConversationHandler,
    CallbackQueryHandler
)

load_dotenv()
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_TELEGRAM_ID")) if os.getenv("ADMIN_TELEGRAM_ID") else None

CHOOSING_SERVICE, GETTING_REQUIREMENTS, GETTING_PHONE = range(3)
WAITING_BROADCAST_MSG = 10

USER_LAST_MESSAGE_TIME = {}
SPAM_LIMIT_SECONDS = 2

# ==================== 🗄️ قاعدة البيانات ====================
DB_FILE = "bot_database.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            full_name TEXT,
            username TEXT,
            joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def add_user_to_db(user_id: int, full_name: str, username: str):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO users (user_id, full_name, username)
        VALUES (?, ?, ?)
        ON CONFLICT(user_id) DO UPDATE SET
            full_name=excluded.full_name,
            username=excluded.username
    ''', (user_id, full_name, username))
    conn.commit()
    conn.close()

def get_all_users():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('SELECT user_id, full_name, username FROM users')
    users = cursor.fetchall()
    conn.close()
    return users

def delete_user_from_db(user_id: int):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM users WHERE user_id = ?', (user_id,))
    conn.commit()
    conn.close()

# ==================================================================

async def check_spam_and_save_user(update: Update) -> bool:
    if not update.effective_user:
        return False
    
    user = update.effective_user
    add_user_to_db(user.id, user.full_name or "", user.username or "")

    current_time = time.time()
    if user.id in USER_LAST_MESSAGE_TIME:
        elapsed_time = current_time - USER_LAST_MESSAGE_TIME[user.id]
        if elapsed_time < SPAM_LIMIT_SECONDS:
            if update.message:
                await update.message.reply_text("⚠️ يرجى عدم إرسال الرسائل بسرعة كبيرة لحماية النظام.")
            return True
            
    USER_LAST_MESSAGE_TIME[user.id] = current_time
    return False

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if await check_spam_and_save_user(update): return
    
    user = update.effective_user
    welcome_text = (
        f"👋 أهلاً بك يا {user.first_name} في منصتنا الاحترافية لتطوير البرمجيات!\n\n"
        "🚀 نحن هنا لتحويل أفكارك إلى واقع رقمي مبهر (مواقع وبوتات متطورة).\n"
        "الرجاء اختيار أحد العروض أو الخدمات من الأزرار أدناه:"
    )
    
    keyboard = [
        [KeyboardButton("🤖 عرض تصميم البوتات"), KeyboardButton("🌐 عرض تصميم المواقع")],
        [KeyboardButton("📢 قناتنا وعروضنا الحصرية"), KeyboardButton("💼 محفظة أعمالنا")],
        [KeyboardButton("💬 إرسال استفسار/طلب مخصص")]
    ]
    
    if ADMIN_ID and user.id == ADMIN_ID:
        keyboard.append([KeyboardButton("⚙️ لوحة التحكم الإدارية")])

    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)
    await update.message.reply_text(welcome_text, reply_markup=reply_markup)

async def handle_menu_options(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if await check_spam_and_save_user(update): return
    
    text = update.message.text
    
    if text == "⚙️ لوحة التحكم الإدارية" or "لوحة التحكم" in text:
        await admin_panel(update, context)
        return

    if text == "🤖 عرض تصميم البوتات":
        bot_text = (
            "🤖 **خدمات تصميم وتطوير البوتات:**\n\n"
            "• بوتات تليجرام خدمية، إدارية، ومتاجر إلكترونية كاملة.\n"
            "• حماية قصوى ضد الاختراق والسبام مع لوحات تحكم متطورة.\n"
            "• ربط ذكي مع قواعد البيانات وتحديثات فورية.\n\n"
            "👇 لبدء طلبك الخاص وتحديد مواصفات بوتك، اضغط على زر (💬 إرسال استفسار/طلب مخصص)."
        )
        await update.message.reply_text(bot_text, parse_mode="Markdown")
        
    elif text == "🌐 عرض تصميم المواقع":
        web_text = (
            "🌐 **خدمات تصميم وتطوير المواقع:**\n\n"
            "• مواقع تعريفية، متاجر إلكترونية، وأنظمة لوحات تحكم (Dashboard).\n"
            "• تصميم عصري متوافق مع الهواتف وشاشات الكمبيوتر.\n"
            "• سرعة فائقة وأكواد نظيفة مجهزة لمحركات البحث (SEO).\n\n"
            "👇 لبدء طلبك وتحديد مواصفات موقعك، اضغط على زر (💬 إرسال استفسار/طلب مخصص)."
        )
        await update.message.reply_text(web_text, parse_mode="Markdown")
        
    elif text == "📢 قناتنا وعروضنا الحصرية":
        channel_text = (
            "📢 **مرحباً بك في منصة المطور الذكي!**\n\n"
            "انضم إلى قناتنا الرسمية لتطلع على أحدث العروض والخدمات البرمجية والحلول الذكية 👇"
        )
        keyboard = [[InlineKeyboardButton("🔗 اضغط هنا للانضمام إلى القناة", url="https://t.me/EngAbuHalima_Channel")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(channel_text, reply_markup=reply_markup, parse_mode="Markdown", disable_web_page_preview=True)

    elif text == "💼 محفظة أعمالنا":
        portfolio_text = (
            "💼 **بعض من أعمالنا السابقة المميزة:**\n\n"
            "• موقع 'مستقبلك معنا' التعليمي المتكامل.\n"
            "• أنظمة إدارة قواعد بيانات ذكية وسريعة الاستجابة.\n"
            "• بوتات إدارة مجموعات وقنوات ضخمة.\n\n"
            "نحن نضمن لك عملاً يشرفك أمام عملائك ومبرمجيك!"
        )
        await update.message.reply_text(portfolio_text)

# ==================== 📝 نظام الطلبات المرن ====================

async def start_order_flow(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if await check_spam_and_save_user(update): return
    await update.message.reply_text("📝 ممتاز! دعنا نجهز طلبك الاحترافي.\nأولاً، ما هو نوع الخدمة التي تريدها؟ (اكتب مثلاً: تصميم موقع، أو تصميم بوت، أو استفسار عام)")
    return CHOOSING_SERVICE

async def get_service_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['service_type'] = update.message.text
    await update.message.reply_text("✍️ رائع جداً. الآن تفضل بكتابة متطلباتك بالتفصيل (اشرح فكرتك، الميزات التي تريدها، وأي تفاصيل أخرى):")
    return GETTING_REQUIREMENTS

async def get_requirements(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['requirements'] = update.message.text
    
    # أزرار خيارات التواصل المريحة والآمنة للعميل
    keyboard = [
        [KeyboardButton("📱 مشاركة رقم الهاتف تلقائياً", request_contact=True)],
        [KeyboardButton("💬 التواصل عبر يوزر التليجرام فقط")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    
    privacy_notice = (
        "🔒 **خيارات التواصل الخصوصية والآمنة:**\n\n"
        "يرجى اختيار طريقة التواصل المناسبة لك:\n"
        "• يمكنك **مشاركة الرقم** تلقائياً أو كتابته يدوياً.\n"
        "• أو اختيار **التواصل عبر يوزر التليجرام** دون إرسال رقم الهاتف.\n\n"
        "🛡️ *جميع بياناتك مشفرة ومحفوظة بأمان لأغراض متابعة طلبك فقط.*"
    )
    
    await update.message.reply_text(privacy_notice, reply_markup=reply_markup, parse_mode="Markdown")
    return GETTING_PHONE

async def get_phone_and_finish(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    
    # التعامل مع خيارات التواصل المخفية والآمنة
    if update.message.contact:
        contact_info = f"📱 رقم الهاتف: `{update.message.contact.phone_number}`"
    elif update.message.text == "💬 التواصل عبر يوزر التليجرام فقط":
        if user.username:
            contact_info = f"💬 عبر يوزر التليجرام: @{user.username}"
        else:
            contact_info = f"💬 عبر حساب التليجرام المباشر (ID: `{user.id}`)"
    else:
        contact_info = f"📝 الوسيلة المدخلة: `{update.message.text}`"

    service = context.user_data.get('service_type')
    reqs = context.user_data.get('requirements')

    keyboard = [
        [KeyboardButton("🤖 عرض تصميم البوتات"), KeyboardButton("🌐 عرض تصميم المواقع")],
        [KeyboardButton("📢 قناتنا وعروضنا الحصرية"), KeyboardButton("💼 محفظة أعمالنا")],
        [KeyboardButton("💬 إرسال استفسار/طلب مخصص")]
    ]
    if ADMIN_ID and user.id == ADMIN_ID:
        keyboard.append([KeyboardButton("⚙️ لوحة التحكم الإدارية")])

    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(
        "✅ تم استلام طلبك بنجاح وبشكل آمن تماماً!\n"
        "سيقوم فريقنا البرمجي بمراجعة التفاصيل والتواصل معك في أقرب وقت ممكن. شكراً لثقتك بنا ✨",
        reply_markup=reply_markup
    )

    if ADMIN_ID:
        order_msg = (
            "🚨 **وصلك طلب جديد ومحمي!** 🚨\n\n"
            f"👤 **العميل:** {user.full_name}\n"
            f"🆔 **معرف العميل:** `{user.id}`\n"
            f"📱 **يوزر التليجرام:** @{user.username if user.username else 'لا يوجد'}\n"
            f"📞 **وسيلة التواصل:** {contact_info}\n"
            f"🛠️ **نوع الخدمة:** {service}\n\n"
            f"📋 **المتطلبات التفصيلية:**\n{reqs}"
        )
        try:
            await context.bot.send_message(chat_id=ADMIN_ID, text=order_msg, parse_mode="Markdown")
        except Exception as e:
            print(f"فشل إرسال الطلب للأدمن: {e}")

    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("تم إلغاء العملية الجارية بنجاح.")
    return ConversationHandler.END

# ==================== 👑 لوحة التحكم والإذاعة ====================

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not ADMIN_ID or user.id != ADMIN_ID:
        if update.message: await update.message.reply_text("⛔ عفواً، هذه اللوحة مخصصة لإدارة النظام فقط.")
        return

    users_count = len(get_all_users())
    text = (
        "⚙️ **مرحباً بك في لوحة تحكم البوت:**\n\n"
        f"👥 **إجمالي المستخدمين في قاعدة البيانات:** {users_count}\n"
        "اختر الإجراء المطلوب من الأزرار أدناه:"
    )
    keyboard = [
        [InlineKeyboardButton("📊 إحصائيات النظام", callback_data="admin_stats")],
        [InlineKeyboardButton("👥 قائمة المستخدمين وحذفهم", callback_data="admin_users")],
        [InlineKeyboardButton("📢 إرسال رسالة جماعية (Broadcast)", callback_data="admin_broadcast")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.message:
        await update.message.reply_text(text, parse_mode="Markdown", reply_markup=reply_markup)
    elif update.callback_query:
        await update.callback_query.edit_message_text(text, parse_mode="Markdown", reply_markup=reply_markup)

async def admin_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "admin_stats":
        total_users = len(get_all_users())
        stats_msg = f"📈 **إحصائيات النظام:**\n\n• إجمالي المستخدمين المسجلين: {total_users}"
        await query.edit_message_text(stats_msg, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 العودة للوحة", callback_data="admin_main")]]))

    elif data == "admin_users":
        users = get_all_users()
        if not users:
            await query.edit_message_text("👥 لا يوجد مستخدمون حالياً في قاعدة البيانات.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 العودة للوحة", callback_data="admin_main")]]))
            return
        
        keyboard = []
        for uid, name, uname in users:
            if uid != ADMIN_ID:
                display_name = name if name else f"User {uid}"
                keyboard.append([InlineKeyboardButton(f"❌ حذف: {display_name}", callback_data=f"del_usr_{uid}")])
        
        keyboard.append([InlineKeyboardButton("🔙 العودة للوحة", callback_data="admin_main")])
        await query.edit_message_text("👥 **إدارة وحذف المستخدمين:**", reply_markup=InlineKeyboardMarkup(keyboard))

    elif data.startswith("del_usr_"):
        uid_to_delete = int(data.split("_")[2])
        delete_user_from_db(uid_to_delete)
        await query.edit_message_text(f"✅ تم حذف المستخدم `{uid_to_delete}` بنجاح!", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 العودة للوحة", callback_data="admin_main")]]))

    elif data == "admin_broadcast":
        await query.edit_message_text(
            "📢 **إرسال رسالة جماعية:**\n\n"
            "تفضل بكتابة الرسالة التي تريد إرسالها لجميع مستخدمي البوت الآن:\n\n"
            "📌 *أو أرسل /cancel لإلغاء الإذاعة.*"
        )
        return WAITING_BROADCAST_MSG

    elif data == "admin_main":
        await admin_panel(update, context)

async def send_broadcast_msg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    broadcast_text = update.message.text
    users = get_all_users()
    
    success_count = 0
    fail_count = 0
    
    status_msg = await update.message.reply_text("⏳ جاري إرسال الرسالة الجماعية لكل المستخدمين...")

    for uid, name, uname in users:
        try:
            await context.bot.send_message(chat_id=uid, text=broadcast_text, parse_mode="Markdown")
            success_count += 1
            time.sleep(0.05)
        except Exception as e:
            fail_count += 1
            print(f"لم نتمكن من الإرسال للمستخدم {uid}: {e}")

    report = (
        "✅ **اكتملت عملية الإذاعة الجماعية بنجاح!**\n\n"
        f"📊 **النتائج:**\n"
        f"• تم الإرسال بنجاح إلى: {success_count} مستخدم\n"
        f"• فشل الإرسال إلى: {fail_count} (غالباً قاموا بحظر البوت)"
    )
    await status_msg.edit_text(report, parse_mode="Markdown")
    return ConversationHandler.END

def main():
    init_db()
    if not BOT_TOKEN:
        print("❌ خطأ: لم يتم العثور على TELEGRAM_BOT_TOKEN")
        return

    app = Application.builder().token(BOT_TOKEN).build()

    broadcast_handler = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(admin_callback_handler, pattern="^admin_broadcast$")
        ],
        states={
            WAITING_BROADCAST_MSG: [MessageHandler(filters.TEXT & ~filters.COMMAND, send_broadcast_msg)]
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(broadcast_handler)
    app.add_handler(CommandHandler("admin", admin_panel))
    app.add_handler(CallbackQueryHandler(admin_callback_handler))

    conv_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Text("💬 إرسال استفسار/طلب مخصص"), start_order_flow)],
        states={
            CHOOSING_SERVICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_service_type)],
            GETTING_REQUIREMENTS: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_requirements)],
            GETTING_PHONE: [MessageHandler(filters.TEXT | filters.CONTACT, get_phone_and_finish)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(conv_handler)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_menu_options))

    print("⚡ البوت الذكي يعمل الآن بنظام التواصل المرن وحماية الخصوصية...")
    app.run_polling()

if __name__ == "__main__":
    main()