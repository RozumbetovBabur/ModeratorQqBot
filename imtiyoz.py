from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackContext
from datetime import datetime
from database import get_connection, release_connection, db_pool

def is_admin(user_id):
    conn = db_pool.getconn()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT group_id FROM admin WHERE user_id = %s", (user_id,))
        rows = cursor.fetchall()
        return [row[0] for row in rows]
    finally:
        cursor.close()
        db_pool.putconn(conn)


def handle_grant_privilege(update, context):
    query = update.callback_query
    query.answer()
    admin_id = query.from_user.id

    group_ids = is_admin(admin_id)
    if not group_ids:
        query.edit_message_text("❗ Siz hesh qanday gruppada admin emessiz.")
        return

    group_id = group_ids[0]

    conn = None
    cursor = None
    try:
        conn = db_pool.getconn()
        cursor = conn.cursor()
        cursor.execute("SELECT user_id, full_name FROM users WHERE group_id = %s", (group_id,))
        users = cursor.fetchall()
    except Exception as e:
        print(f"[handle_grant_privilege] Xatolik: {e}")
        query.edit_message_text("❌ qátelik juz berdi.")
        return

    finally:
        if cursor: cursor.close()
        if conn: db_pool.putconn(conn)

    if not users:
        query.edit_message_text("❗ Gruppa ushın hesh qanday paydalanıwshı tabılmadı.")
        return

    buttons = []
    for user_id, full_name in users:
        label = full_name if full_name else str(user_id)
        buttons.append([
            InlineKeyboardButton(f"👤 {label}", callback_data=f"give_priv:{user_id}:{group_id}")
        ])

    reply_markup = InlineKeyboardMarkup(buttons)
    context.bot.send_message(
        chat_id=query.from_user.id,
        text="✅ Jeńillik bermekshi bolǵan paydalanıwshın saylań:",
        reply_markup=reply_markup
    )

def handle_privilege_selection(update, context):
    query = update.callback_query
    query.answer()

    data = query.data
    if not data.startswith("give_priv:"):
        return

    try:
        parts = data.split(":")
        user_id = int(parts[1])
        group_id = int(parts[2])
    except (IndexError, ValueError):
        query.edit_message_text("❌ Qátelik: Maǵlıwmat durıs emes.")
        return

    conn = None
    cursor = None
    try:
        conn = db_pool.getconn()
        cursor = conn.cursor()

        cursor.execute("SELECT username, full_name FROM users WHERE user_id = %s AND group_id = %s", (user_id, group_id))
        result = cursor.fetchone()
        if result:
            username, full_name = result
        else:
            query.edit_message_text("❌ Paydalanıwshı tabılmadı.")
            return

        granted_at = datetime.now()

        cursor.execute('''
            INSERT INTO imtiyozli_users (user_id, username, group_id, granted_at)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (user_id, group_id) DO NOTHING
        ''', (user_id, username, group_id, granted_at))

        conn.commit()

        display_name = f"{username}" if username else full_name

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("⬅️ Arqaǵa", callback_data="back_to_admin_panel")]
        ])

        query.edit_message_text(
            text=f"✅ Jeńillik {display_name} paydalanıwshıǵa mumkinshilik tabıslı berildi.",
            reply_markup=keyboard
        )

    except Exception as e:
        print(f"[handle_privilege_selection] Xatolik: {e}")
        query.edit_message_text("❌ ishki qátelik juz berdi.")
    finally:
        if cursor: cursor.close()
        if conn: db_pool.putconn(conn)