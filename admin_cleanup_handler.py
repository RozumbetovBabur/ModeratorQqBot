# admin_cleanup_handler.py
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackContext
from database import is_admin, clear_invited_counts_by_group_ids
from admin_panel import build_admin_panel

def handle_admin_cleanup(update,context):
    query = update.callback_query
    user_id = query.from_user.id
    group_ids = is_admin(user_id)

    if not group_ids:
        query.answer("❌ Sizde ruxsat joq")
        return

    text = (
        "⚠️ <b>Eskertiw!</b>\n\n"
        "Bul ámel siz admınıstrator bolǵan gruppadaǵı barlıq paydalanıwshılardıń <b>" 
        "qosqan jańa paydalanıwshılar sanın (invited_count)</b> 0 ge ornatadı.\n\n"
        "Dawam etiwdi qáleysizbe?"
    )

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ Awa, tazalaw", callback_data="confirm_cleanup"),
            InlineKeyboardButton("❌ yaq, bıykar etiw", callback_data="cancel_cleanup")
        ]
    ])

    query.edit_message_text(text=text, parse_mode="HTML", reply_markup=keyboard)

def confirm_cleanup(update,context):
    query = update.callback_query
    query.answer()

    user_id = query.from_user.id
    group_ids = is_admin(user_id)

    if group_ids:
        clear_invited_counts_by_group_ids(group_ids)
        query.edit_message_text(
            "✅ <b>Tazalaw tabıslı atqarıldı!</b>\n\n"
            "Barlıq <b>invited_count</b> bahaları 0 ge ornatildi.",
            parse_mode='HTML'
        )

        # Keyin admin panelga qaytamiz
        message_text, keyboard = build_admin_panel(user_id)
        context.bot.send_message(
            chat_id=query.message.chat_id,
            text=message_text,
            parse_mode='HTML',
            reply_markup=keyboard
        )
    else:
        query.edit_message_text("❌ Sizde ruxsat joq.")


def cancel_cleanup(update,context):
    query = update.callback_query
    query.answer()
    user_id = query.from_user.id
    message_text, keyboard = build_admin_panel(user_id)

    query.edit_message_text(
        text=message_text,
        parse_mode='HTML',
        reply_markup=keyboard
    )

