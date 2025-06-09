from telegram import BotCommand
from telegram.ext import Updater, MessageHandler, CallbackQueryHandler, CommandHandler, Filters, ChatMemberHandler
from config import TOKEN
from handlers import handle_new_members, handle_member_update, handle_new_message, handle_check_invites, handle_start, handle_member_update
from database import init_db
from admin_panel import get_admin_panel_handler, admin_stats_handler, back_to_admin_panel, handle_admin_users
from admin_cleanup_handler import handle_admin_cleanup, confirm_cleanup, cancel_cleanup
from admin_usercount_handler import handle_usercount, receive_usercount, usercount_conv_handler, back_to_admin
from help import help_command
import os
import sys
from dotenv import load_dotenv
import logging

# .env faylidan o'zgaruvchilarni yuklab olamiz
load_dotenv()
token = os.getenv("BOT_TOKEN")


def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler("bot.log"),
            logging.StreamHandler(sys.stdout)
        ]
    )
    init_db()
    updater = Updater(token=token, use_context=True)
    dp = updater.dispatcher

    # === Bot komandalarini ro‘yxatdan o‘tkazish ===
    commands = [
        BotCommand("start", "🟢 Botni iske túsiriw / Запустить бота"),
        BotCommand("admin", "⚙️ admin paneldi sazlaw / настройка панели администратора"),
        BotCommand("help", "📓 Botdıń buyuqları / Величие бота")
    ]
    updater.bot.set_my_commands(commands)

    dp.add_handler(CommandHandler("start", handle_start))
    dp.add_handler(CommandHandler("help", help_command))
    # Neshe paydalanuwshilardi sanab beredi
    dp.add_handler(MessageHandler(Filters.status_update.new_chat_members, handle_new_members))

    # Statistika komandasi
    dp.add_handler(MessageHandler(Filters.text & Filters.chat_type.groups, handle_new_message))
    # Inline tugma orqali ko‘rish
    dp.add_handler(CallbackQueryHandler(handle_check_invites, pattern='check_invites'))
    # Guruhga qo‘shilganlarni nazorat qilish
    dp.add_handler(ChatMemberHandler(handle_member_update, ChatMemberHandler.CHAT_MEMBER))

    # 🔐 Admin panel handler
    dp.add_handler(get_admin_panel_handler())

    dp.add_handler(CallbackQueryHandler(admin_stats_handler, pattern='^admin_stats$'))
    dp.add_handler(CallbackQueryHandler(back_to_admin_panel, pattern='^back_to_admin_panel$'))
    dp.add_handler(CallbackQueryHandler(handle_admin_users, pattern='^admin_users$'))

    dp.add_handler(CallbackQueryHandler(handle_admin_cleanup, pattern='admin_cleanup'))
    dp.add_handler(CallbackQueryHandler(confirm_cleanup, pattern='confirm_cleanup'))
    dp.add_handler(CallbackQueryHandler(cancel_cleanup, pattern='cancel_cleanup'))

    dp.add_handler(CallbackQueryHandler(handle_usercount, pattern='^admin_usercount$'))
    dp.add_handler(CallbackQueryHandler(back_to_admin, pattern='^back_to_admin$'))
    dp.add_handler(usercount_conv_handler)


    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
