# admin_usercount_handler.py
# Callback handler uchun
from admin_panel import build_admin_panel
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackContext, MessageHandler, Filters
from database import is_admin, get_connection, release_connection, db_pool
import psycopg2


# Matn yuborish bosqichi
def handle_usercount(update,context):
    user_id = update.effective_user.id
    group_ids = is_admin(user_id)

    if not group_ids:
        update.callback_query.answer("Sizge ruhsat joq.", show_alert=True)
        return

    context.user_data['group_ids'] = group_ids

    update.callback_query.message.edit_text(
        "📌 Iltimas, siz toparlarǵa qosıwshı bolǵan jańa paydalanıwshılar sanın kiritiń.\n"
        "Tek san kórinisinde kiritiń (mısalı : 25)"
    )

    context.user_data['awaiting_usercount'] = True


def receive_usercount(update,context):
    if not context.user_data.get('awaiting_usercount'):
        return

    try:
        count = int(update.message.text)
    except ValueError:
        update.message.reply_text("❌ Iltimas, tek san kiritiń. Mısalı : 25")
        return

    group_ids = context.user_data.get('group_ids')
    if not group_ids:
        update.message.reply_text("❌ Toparlar tabılmadı.")
        return

    conn = None
    cursor = None

    try:
        # PostgreSQL ga ulanish
        conn = db_pool.getconn()
        cursor = conn.cursor()

        # Jadval yaratish (agar hali mavjud bo‘lmasa)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS planned_invites (
                group_id BIGINT PRIMARY KEY,
                planned_count INTEGER
            )
        ''')

        # Har bir group_id uchun upsert qilish
        for gid in group_ids:
            cursor.execute('''
                INSERT INTO planned_invites (group_id, planned_count)
                VALUES (%s, %s)
                ON CONFLICT (group_id)
                DO UPDATE SET planned_count = EXCLUDED.planned_count
            ''', (gid, count))

        # Guruh nomlarini yig'ish
        group_lines = ""
        for gid in group_ids:
            cursor.execute("SELECT group_name FROM groups WHERE group_id = %s", (gid,))
            result = cursor.fetchone()
            group_name = result[0] if result else f"ID: {gid}"
            group_lines += f"- <b>{group_name}</b> → <b>{count}</b>\n"

        conn.commit()

    except Exception as e:
        print(f"[receive_usercount] Xatolik: {e}")
        update.message.reply_text("❌ Xatolik yuz berdi.")
        return

    finally:
        if cursor:
            cursor.close()
        if conn:
            db_pool.putconn(conn)

    context.user_data['awaiting_usercount'] = False

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("⬅️ Arqaǵa", callback_data="back_to_admin")]
    ])

    update.message.reply_text(
        f"✅ <b>Maǵlıwmatlar tabıslı saqlandi!</b>\n\n"
        f"Tómendegi toparlarǵa san jazıldı:\n{group_lines}",
        parse_mode='HTML',
        reply_markup=keyboard
    )


def back_to_admin(update,context):
    query = update.callback_query
    query.answer()
    user_id = query.from_user.id
    message_text, keyboard = build_admin_panel(user_id)

    query.edit_message_text(
        text=message_text,
        parse_mode='HTML',
        reply_markup=keyboard
    )


# Main.py ichiga qo‘shiladigan handlerlar
usercount_conv_handler = MessageHandler(Filters.text & ~Filters.command, receive_usercount)
