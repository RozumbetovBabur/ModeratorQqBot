from telegram import Update
from telegram.ext import CallbackContext

def help_command(update, context):
    help_text = (
        "🤖 *Bot Xızmetleri Haqqında Tolıq Qóllanba*\n\n"
        "📌 Bul bot arqalı siz toparıńızdı basqarıwıńız, statistika kóriwińiz hám"
        "Paydalanıwshılar ústinen qadaǵalaw ornatıwıńız múmkin. Tómende botimizning barlıq zárúrli buyrıqları hám olardıń wazıypaları keltirilgen:\n\n"

        "🟢 /start — Botdı jumısqa tusiredi hám sizdi bot xızmetlerin menen tanıstıradı.\n\n"

        "🛠 /admin — Adminler ushın arnalǵan basqarıw paneli. Ol arqalı siz tómendegi xızmetlerden paydalanıwıńız múmkin:\n\n"

        "1️⃣ 📊 *Statistika* — Gruppada neshe aǵza bar ekenligi, neshe admin bar ekenligi hám adminler neshe gruppaǵa huquqı barlıǵın kórsetedi.\n\n"
        "2️⃣ 👥 *Paydalanıwshılar* - Gruppaǵa qosılǵan aǵzalardı dizimin kóriw hám basqarıw imkaniyatın beredi.\n\n"
        "3️⃣ 🗑 *Gruppadan tazalaw* - Gruppada aktiv emes yamasa májburiy qosılǵan aǵzalardı sanın tazalaw múmkinshiligi bar.\n\n"
        "4️⃣ 👥 *Paydalanıwshı sonı* - Hár bir gruppa ushın neshe dana paydalanıwshı limit qoyıw kerekligini belgilew imkaniyatın beredi.\n\n"

        "❗️Esletpe: Buyrıqlar tek kerekli ruxsat hám adminlikka iye paydalanıwshılar ushın isleydi. Gruppanı tolıq basqarıw ushın siz botga adminlik huqıqın bergenińizge isenim payda etiń.\n\n"

        "🔐 Sistema qawipsizligi hám paydalanıwshılar maǵlıwmatları mudami qorǵawda!\n\n"
        "📞 Járdem kerek bolsa - /help buyrıǵın qayta jiberiń yamasa adminlerge xabar beriń: @BaburDevBot"
    )

    update.message.reply_text(help_text, parse_mode='Markdown')
