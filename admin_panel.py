# admin_panel.py
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackContext, CommandHandler
import psycopg2
from database import is_admin, get_group_names, get_group_users, get_users_by_date_range, get_users_by_exact_range, get_connection, release_connection, db_pool

def build_admin_panel(user_id):
    group_ids = is_admin(user_id)
    if not group_ids:
        return None, None

    group_names = get_group_names(group_ids)
    formatted_names = "\n".join([f"📌 <b>{name}</b>" for name in group_names])
    message_text = (
        "🛠 <b>Admin panel</b>\n\n"
        f"{formatted_names}\n\n"
        "Ústinde kórsetilgen gruppalar siz admınıstratorlik qılıp atırǵan toparlar bolıp tabıladı.\n"
        "Iltimas kerekli tuymeni saylań :"
    )

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📊 Statistika", callback_data="admin_stats"),
            InlineKeyboardButton("👥 Paydalanıwshılar", callback_data="admin_users"),
        ],
        [
            InlineKeyboardButton("🗑 Gruppalardi tazalaw", callback_data="admin_cleanup"),
            InlineKeyboardButton("👥 Paydalanıwshı san", callback_data="admin_usercount"),
        ],
        [
            InlineKeyboardButton("🎖 Jeńillik beriw", callback_data="grant_privilege"),  # ✅ Qo‘shildi
        ],
    ])

    return message_text, keyboard


def handle_admin_panel(update,context):
    user_id = update.effective_user.id
    message_text, keyboard = build_admin_panel(user_id)

    if not message_text:
        update.message.reply_text("❌ Siz bul bólimge kire almaysız.")
        return

    update.message.reply_text(
        message_text,
        parse_mode='HTML',
        reply_markup=keyboard
    )

def admin_stats_handler(update,context):
    query = update.callback_query
    query.answer()
    user_id = query.from_user.id
    message = query.message
    chat_id = message.chat_id

    conn = None
    cursor = None

    try:
        # PostgreSQL pooldan ulanish olish
        conn = db_pool.getconn()
        cursor = conn.cursor()

        # Ushbu admin qaysi group_idda admin — aniqlaymiz
        cursor.execute("SELECT group_id FROM admin WHERE user_id = %s", (user_id,))
        row = cursor.fetchone()

        if not row:
            query.edit_message_text("⛔ Siz admin emessiz yamasa gruppa tabılmadı.")
            return

        group_id = row[0]

        # Foydalanuvchilar soni shu group_id bo‘yicha
        cursor.execute("SELECT COUNT(*) FROM users WHERE group_id = %s", (group_id,))
        user_count = cursor.fetchone()[0]

        # Adminlar soni shu group_id bo‘yicha
        cursor.execute("SELECT COUNT(*) FROM admin WHERE group_id = %s", (group_id,))
        admin_count = cursor.fetchone()[0]

        # Bu admin nechtada admin?
        cursor.execute("SELECT COUNT(DISTINCT group_id) FROM admin WHERE user_id = %s", (user_id,))
        groups_for_admin = cursor.fetchone()[0]

        # Bog'lanishni yopamiz
        conn.commit()

        # Shiroyli matn
        text = (
            f"📊 <b>Statistika</b>\n"
            f"────────────────────\n"
            f"👥 <b>Guruppaǵa jazǵan paydalanıwshılardıń sanı:</b> <code>{user_count}</code>\n"
            f"👮 <b>Adminler sanı:</b> <code>{admin_count}</code>\n"
            f"🔁 <b>Siz admin bolǵan gruppalar:</b> <code>{groups_for_admin}</code>\n"
        )

        # Orqaga tugmasi
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("⬅️ Arqaǵa", callback_data="back_to_admin_panel")]
        ])

        query.edit_message_text(text=text, parse_mode="HTML", reply_markup=keyboard)

    except Exception as e:
        print(f"[admin_stats_handler] Xatolik: {e}")
        query.edit_message_text("❌ Ichki xatolik yuz berdi.")

    finally:
        if cursor:
            cursor.close()
        if conn:
            db_pool.putconn(conn)

def back_to_admin_panel(update,context):
    query = update.callback_query
    query.answer()
    user_id = query.from_user.id

    message_text, keyboard = build_admin_panel(user_id)

    if not message_text:
        query.edit_message_text("❌ Siz bul bólimge kire almaysız.")
        return

    query.edit_message_text(
        message_text,
        parse_mode='HTML',
        reply_markup=keyboard
    )

def handle_admin_users(update,context):
    query = update.callback_query
    user_id = query.from_user.id
    query.answer()

    group_ids = is_admin(user_id)
    if not group_ids:
        query.edit_message_text("❌ Sizge bul bólimge kiriwge ruxsat joq.")
        return

    users = get_group_users(group_ids)

    if not users:
        query.edit_message_text("Bul gruppalarda hesh qanday paydalanıwshılar joq.")
        return

    message = "<b>👥 Gruppa paydalanıwshıları:</b>\n\n"
    for i, user in enumerate(users, 1):
        full_name = user[0] or "atı joq"
        username = f"@{user[1]}" if user[1] else "Username joq"
        invited = user[2] or 0
        message += f"<b>{i}.</b> {full_name} | {username} | Usınıs etkenler: <b>{invited}</b>\n"

    # Orqaga tugmasi
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📊 1 kúnlik", callback_data="report_day"), InlineKeyboardButton("📊 1 háptelik", callback_data="report_week")],
        [InlineKeyboardButton("📊 1 aylıq", callback_data="report_month"), InlineKeyboardButton("📊 1 Jıllıq", callback_data="report_year")],
        [InlineKeyboardButton("⬅️ Arqaǵa", callback_data="back_to_admin_panel")]
    ])

    query.edit_message_text(
        text=message,
        parse_mode='HTML',
        reply_markup=keyboard
    )

def handle_time_based_report(update,context):
    query = update.callback_query
    query.answer()
    user_id = query.from_user.id
    data = query.data

    group_ids = is_admin(user_id)
    if not group_ids:
        query.edit_message_text("❌ Sizge bul bólimge kiriwge ruxsat joq.")
        return

    # Vaqt oraliqlarini belgilang
    if data == "report_day":
        title = "📊 1 kúnlikdi kórsetedi"
        from_days, to_days = 0, 1
        no_users_msg = "📅 Búginlik esabatında : paydalanıwshılar gruppaǵa qosılmaǵan."
    elif data == "report_week":
        title = "📊 1 háptelikdi kórsetedi"
        from_days, to_days = 1, 7
        no_users_msg = "📅 1 háptelik esabatında: paydalanıwshılar gruppaǵa qosılmaǵan."
    elif data == "report_month":
        title = "📊 1 aylıqdi kórsetedi"
        from_days, to_days = 7, 30
        no_users_msg = "📅 1 aylıq esabatında: paydalanıwshılar gruppaǵa qosılmaǵan."
    elif data == "report_year":
        title = "📊 1 Jılliqdi kórsetedi"
        from_days, to_days = 30, 365
        no_users_msg = "📅 1 jılliq esabatında: paydalanıwshılar gruppaǵa qosılmaǵan."
    else:
        return

    users = get_users_by_exact_range(group_ids, from_days, to_days)

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("⬅️ Arqaǵa", callback_data="report_back")]
    ])

    if not users:
        # query.edit_message_text(f"{title} – hesh qanday paydalanıwshı qosılmagan.")
        query.edit_message_text(no_users_msg, reply_markup=keyboard)
        return

    message = f"<b>{title}:</b>\n\n"
    for i, user in enumerate(users, 1):
        full_name = user[0] or "Atı joq"
        username = f"@{user[1]}" if user[1] else "Username joq"
        invited = user[2] or 0
        joined_at = user[3] or "Waqtı anıq emes"
        message += f"<b>{i}.</b> {full_name} | {username} | Qosılǵanlar: <b>{invited}</b> | Qosılǵanlar: {joined_at}\n"



    query.edit_message_text(
        text=message,
        parse_mode='HTML',
        reply_markup=keyboard
    )

def get_admin_panel_handler():
    return CommandHandler("admin", handle_admin_panel)
