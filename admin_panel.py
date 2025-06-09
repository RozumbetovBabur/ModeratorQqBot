# admin_panel.py
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext, CommandHandler
from telegram import Update
import sqlite3

from database import is_admin, get_group_names, get_group_users

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
    ])

    return message_text, keyboard


def handle_admin_panel(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    message_text, keyboard = build_admin_panel(user_id)

    if not message_text:
        update.message.reply_text("❌ Siz bul bólimge kirey almaysız.")
        return

    update.message.reply_text(
        message_text,
        parse_mode='HTML',
        reply_markup=keyboard
    )

def admin_stats_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    user_id = query.from_user.id
    message = query.message
    chat_id = message.chat_id

    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()

    # Ushbu admin qaysi group_idda admin — aniqlaymiz
    cursor.execute("SELECT group_id FROM admin WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()

    if not row:
        query.edit_message_text("⛔ Siz admin emessiz yamasa gruppa tabılmadı.")
        return

    group_id = row[0]

    # Foydalanuvchilar soni shu group_id bo‘yicha
    cursor.execute("SELECT COUNT(*) FROM users WHERE group_id = ?", (group_id,))
    user_count = cursor.fetchone()[0]

    # Adminlar soni shu group_id bo‘yicha
    cursor.execute("SELECT COUNT(*) FROM admin WHERE group_id = ?", (group_id,))
    admin_count = cursor.fetchone()[0]

    # Bu admin nechtada admin?
    cursor.execute("SELECT COUNT(DISTINCT group_id) FROM admin WHERE user_id = ?", (user_id,))
    groups_for_admin = cursor.fetchone()[0]

    conn.close()

    # Shiroyli matn
    text = (
        f"📊 <b>Statistika</b>\n"
        f"────────────────────\n"
        f"👥 <b>Paydalanıwshılar sanı:</b> <code>{user_count}</code>\n"
        f"👮 <b>Adminler sanı:</b> <code>{admin_count}</code>\n"
        f"🔁 <b>Siz admin bolǵan gruppalar:</b> <code>{groups_for_admin}</code>\n"
    )

    # Orqaga tugmasi
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("⬅️ Arqaǵa", callback_data="back_to_admin_panel")]
    ])

    query.edit_message_text(text=text, parse_mode="HTML", reply_markup=keyboard)

def back_to_admin_panel(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    user_id = query.from_user.id

    message_text, keyboard = build_admin_panel(user_id)

    if not message_text:
        query.edit_message_text("❌ Siz bul bólimge kirey almaysız.")
        return

    query.edit_message_text(
        message_text,
        parse_mode='HTML',
        reply_markup=keyboard
    )

def handle_admin_users(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = query.from_user.id
    query.answer()

    group_ids = is_admin(user_id)
    if not group_ids:
        query.edit_message_text("❌ Sizge bul bólimge kirisiw ruhsat joq.")
        return

    users = get_group_users(group_ids)

    if not users:
        query.edit_message_text("Bul gruppalarda hesh qanday paydalanıwshı joq.")
        return

    message = "<b>👥 Gruppa paydalanıwshıları:</b>\n\n"
    for i, user in enumerate(users, 1):
        full_name = user[0] or "atı joq"
        username = f"@{user[1]}" if user[1] else "Username joq"
        invited = user[2] or 0
        message += f"<b>{i}.</b> {full_name} | {username} | Usınıs etkenler: <b>{invited}</b>\n"

    # Orqaga tugmasi
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("⬅️ Arqaǵa", callback_data="back_to_admin_panel")]
    ])

    query.edit_message_text(
        text=message,
        parse_mode='HTML',
        reply_markup=keyboard
    )


def get_admin_panel_handler():
    return CommandHandler("admin", handle_admin_panel)
