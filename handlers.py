from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, ChatMember, BotCommand
from telegram.ext import CallbackQueryHandler, MessageHandler, Filters, CommandHandler, CallbackContext
from database import add_user, increment_invite, get_invited_count, get_all_users, save_admin, is_admin_from_db, save_group, get_planned_count_by_group_id


def handle_new_members(update, context):
    message = update.message
    inviter = message.from_user  # Kim qo‘shganini aniqlaydi
    new_members = message.new_chat_members  # Yangi a'zolar ro‘yxati

    # Qo‘shgan odamni bazaga qo‘shamiz (agar mavjud bo‘lmasa)
    inviter_full_name = f"{inviter.first_name or ''} {inviter.last_name or ''}".strip()
    add_user(inviter.id, inviter_full_name)

    added_count = 0

    for member in new_members:
        # O‘zini yoki botni hisoblamaymiz
        if member.id != inviter.id and not member.is_bot:
            added_count += 1

    if added_count > 0:
        increment_invite(inviter.id, added_count)
        count = get_invited_count(inviter.id)
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"{inviter_full_name}, házirge shekem {count} paydalanıwshı qosqansız."
        )
def handle_new_message(update, context):
    user = update.effective_user
    chat_id = update.effective_chat.id
    user_id = user.id

    # 🔍 Guruhda bu user adminmi yoki yo‘qmi — aniqlaymiz
    try:
        member = context.bot.get_chat_member(chat_id, user_id)
        is_admin = member.status in ['administrator', 'creator']
    except Exception as e:
        # print(f"Admin statusında anıqlawda qátelik boldı: {e}")
        is_admin = False

    # ✅ Faqat oddiy odam (na admin, na bot) bo‘lsa bazaga qo‘shamiz
    if not is_admin and not user.is_bot:
        full_name = f"{user.first_name or ''} {user.last_name or ''}".strip()
        username = user.username  # Telegram username (faqat username qismi, @siz)
        group_id = chat_id  # chat_id ni group_id sifatida uzatamiz
        add_user(user_id, full_name, username, group_id)
    else:
        return
        # print(f"{user.full_name} — Admin yamasa bot, bazaǵa qosılmadi.")

    # 👮 Adminlar va botlar uchun boshqa tekshiruv ishlamasin
    if is_admin or user.is_bot:
        return

    # ✋ Agar admin bo‘lmasa, invited_count tekshiruv ishlaydi
    count = get_invited_count(user_id)
    planned_count = get_planned_count_by_group_id(chat_id)
    # print(f"{user.full_name} invited_count: {count}, planned_count: {planned_count}")
    if count < planned_count:
        try:
            context.bot.delete_message(chat_id=chat_id, message_id=update.message.message_id)
        except Exception as e:
            return
            # print(f"Xabardı óshiriwde qátelik: {e}")

        keyboard = [
            [InlineKeyboardButton("Qosqanlardıń dizimin kóriw", callback_data='check_invites')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        context.bot.send_message(
            chat_id=chat_id,
            text=f"👤 {user.full_name}, siz ele {planned_count - count} adam qospaǵansız. "
                 f"guruppaǵa jazıw ushın {planned_count - count} adam qosıw kerek!.",
            reply_markup=reply_markup
        )

def handle_member_update(update, context):
    member = update.chat_member

    # Foydalanuvchi guruhga qo‘shilganini tekshiramiz
    if (
            member.old_chat_member.status in ['left', 'kicked']
            and member.new_chat_member.status == 'member'
    ):
        # Qo‘shilgan foydalanuvchini bazaga qo‘shamiz
        user = member.new_chat_member.user
        add_user(user.id, user.full_name)

        # Uni kim qo‘shgan bo‘lsa, shuni bazaga qo‘shamiz va hisobini oshiramiz
        inviter = member.inviter
        if inviter:
            add_user(inviter.id, inviter.full_name)
            increment_invite(inviter.id)



def handle_check_invites(update, context):
    query = update.callback_query
    user = query.from_user
    chat_id = query.message.chat_id


    count = get_invited_count(user.id)
    planned_count = get_planned_count_by_group_id(chat_id)

    add_user(user.id, user.full_name)  # Foydalanuvchini bazaga qo‘shib qo‘yish

    query.answer()
    query.edit_message_text(
        text=f"👤 {user.full_name}, Siz házirge shekem {count} - paydalanıwshı qosqansız.\n"
             f"Sizge belgilengen limit: {planned_count}"
    )

def handle_start(update: Update, context: CallbackContext):
    chat = update.effective_chat
    bot = context.bot
    user = update.effective_user

    # Faqat guruhda ishga tushsin
    if chat.type not in ["group", "supergroup"]:
        # Inline tugma yaratish
        keyboard = [
            [InlineKeyboardButton("➕ GRUPPAǴA QOSÍLÍW ➕", url=f"https://t.me/{context.bot.username}?startgroup=true")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        update.message.reply_text("🤖 Botdan paydalanıw boyınsha qollanba \n\n"
"Assalawma aleykum! Bul bot gruppańızdaǵı iskerlikti janlandırıw, aǵzalıq rejimin saqlaw hám doslardı gruppaǵa usınıwdı xoshametlew ushın jaratılǵan bot. Tómendegi tártip tiykarında botdan tolıq hám tuwrı paydalanıwıńız múmkin:\n\n"
                                  "1️⃣ Botni gruppaǵa qosıw\n"
                                  " Áwele, botdı gruppańızǵa admin etip qosıwıńız shárt. Sebebi botqa kerekli ruxsatlar bolmasa ol paydalanıwshılardı qadaǵalaw ete almaydı.\n\n"
"✅ Admin ruxsatisiz bot islemeydi!n\n\n"
                                  "2️⃣ /start buyrıǵı arqalı baslaw\n"
"Botdı gruppaǵa qosqannan keyin, gruppada /start buyrıǵın jazıń. Bul buyrıq arqalı bot avtomatikalıq túrde gruppadaǵı adminlerdi anıqlap, olardı arnawlı bazaǵa saqlaydı.\n\n"
                                  "3️⃣ Admin panelge kirisiw\n"
"Admin bolǵan paydalanıwshı botdıń jeke chatına kirip, /admin buyrıǵın tańlawı kerek. 🔐 Tek gruppa adminleri ushın ashıladı!\n\n"
                                  "4️⃣ '👥 Paydalanıwshı sanı' tuymesi\n"
"Admin panel ashılǵannan keyin, '👥 Paydalanıwshı sanı' tuymesi basıladı.\n"
"Bul jerde siz hár bir ápiwayı paydalanıwshıǵa gruppaǵa jazıw huqıqı beriliwi ushın neshe jańa paydalanıwshı usınıwı kerekligin belgileysiz.\n"
"💡 Mısalı : “Hár kim 10 adam usınıs qilsin” dep aytıwıńız múmkin.\n\n"
                                  "5️⃣ Ápiwayı paydalanıwshılar ushın sheklew\n"
"Endi, ápiwayı paydalanıwshı gruppada xabar jazıwshı bolsa, bot olardı tekseredi:\n\n"

"Eger ol ele belgilengen sannı atqarmaǵan bolsa (mısalı, 10 adam qospaǵan bolsa ),\n"
"✋ Bot olardıń xabarın óshiredi hám “Ele {eshe adam} qosqanın kórsetip beredi hám” yadqa saladı.\n"
" 📨 Sonıń menen birge, “Qosqanlardıń dizimin ko'riw” tuymesi arqalı óz jaǵdayın kóriw múmkin.\n\n"
                                  "6️⃣ Doslardı usınıw hám jazıw erkinligi\n"
"Paydalanıwshı kerekli muǵdarda jańa adamlardı gruppaǵa usınıs qilsa, bot avtomatikalıq túrde oǵan gruppaǵa jazıw huqıqın beredi.\n"
"🎉 Qutlıqlaymiz! Siz endi gruppada biymálel qatnasıw imkaniyati jarata alasız!\n\n"
                                  "7️⃣ Hár kim óz jetiskenligin kóriwi múmkin\n"
"Hár bir paydalanıwshı bot xabarları arqalı ózi gruppaǵa neshe adamdı qosqanın biliwi múmkin.\n"
"🧮 Bul jeke statistika sizdiń qanshelli aktiv ekenligińizdi kórsetedi!\n\n"
                                  "8️⃣ Statistika (📊) bólimi - Tolıq analiz\n"
"Admin paneldegi 📊 Statistika tuymesin basıń hám tómendegilerdi biling:\n\n"

"gruppańızda neshe admin bar\n\n"

"Hár bir admin neshe gruppanı basqarıp atır\n\n"

"Gruppada jámi neshe paydalanıwshı bar\n"
"👀 Hámmesi bir aynada - ápiwayılıǵı menen!\n\n"
                                  "9️⃣ 🗑 Esaptı tazalaw \n\n"
" waqtı kelip, paydalanıwshılardıń usınıslar statistikası jańalanmaqshı bolsańız -\n"
"🗑 Gruppadan tazalaw tuymesi arqalı barlıq paydalanıwshılardıń usınıs etkenler sanın nolge túsiriw múmkin\n.\n"
"🧹 Jańa baslanıw ushın paydalı funksiya!\n\n"
                                  "Bul buyrıq tek gruppada isleydi.", reply_markup=reply_markup)
        return

    group_id = chat.id
    group_name = chat.title or "NoName"

    # Guruhni bazaga qo‘shamiz
    save_group(group_id, group_name)

    # Guruhdagi barcha adminlarni aniqlaymiz
    admins = bot.get_chat_administrators(group_id)
    admin_list = []

    for admin in admins:
        admin_user = admin.user
        user_id = admin_user.id
        username = admin_user.username or "NoUsername"
        phone_number = "Unknown"  # Istasangiz kelajakda contact orqali to‘ldirishingiz mumkin

        save_admin(user_id, username, phone_number, group_id)

        admin_list.append(f"👤 {admin_user.full_name} | @{username}")

    admin_text = "\n".join(admin_list)
    update.message.reply_text(
        f"✅ Gruppa: {group_name} ({group_id})\n"
        f"Adminlar bazaga saqlandi:\n\n{admin_text}"
    )


