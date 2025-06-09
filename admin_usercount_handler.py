# admin_usercount_handler.py
import sqlite3
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackContext, MessageHandler, Filters
from database import is_admin


# Matn yuborish bosqichi
def handle_usercount(update: Update, context: CallbackContext):
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


# Son qabul qilish va saqlash
def receive_usercount(update: Update, context: CallbackContext):
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

    # Jadval yaratish va saqlash
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()

    cursor.execute('''CREATE TABLE IF NOT EXISTS planned_invites (
        group_id INTEGER PRIMARY KEY,
        planned_count INTEGER
    )''')

    for gid in group_ids:
        cursor.execute("REPLACE INTO planned_invites (group_id, planned_count) VALUES (?, ?)", (gid, count))

    conn.commit()
    conn.close()

    context.user_data['awaiting_usercount'] = False

    group_lines = "\n".join([f"- <code>{gid}</code> → <b>{count}</b>" for gid in group_ids])
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("⬅️ Arqaǵa", callback_data="back_to_admin")]
    ])

    update.message.reply_text(
        f"✅ <b>Maǵlıwmatlar tabıslı saqlandi!</b>\n\n"
        f"Tómendegi toparlarǵa san jazıldı :\n{group_lines}",
        parse_mode='HTML',
        reply_markup=keyboard
    )


# Callback handler uchun
from admin_panel import build_admin_panel


def back_to_admin(update: Update, context: CallbackContext):
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
