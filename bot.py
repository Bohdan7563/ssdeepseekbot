import os
import logging
import requests
import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# ========== ЗМІННІ СЕРЕДОВИЩА ==========
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
CLOUDFLARE_ACCOUNT_ID = os.environ.get("CLOUDFLARE_ACCOUNT_ID")
CLOUDFLARE_API_TOKEN = os.environ.get("CLOUDFLARE_API_TOKEN")

if not all([TELEGRAM_TOKEN, CLOUDFLARE_ACCOUNT_ID, CLOUDFLARE_API_TOKEN]):
    raise ValueError("❌ Не всі змінні середовища задані! Перевір TELEGRAM_TOKEN, CLOUDFLARE_ACCOUNT_ID, CLOUDFLARE_API_TOKEN")
# ========================================

MODEL = "@cf/meta/llama-3-8b-instruct"

# Психологічні тактики
TACTICS = [
    "Комплімент + питання: зроби комплімент і одразу задай відкрите питання, щоб зацікавити.",
    "Гумор + самоіронія: використай легкий гумор, щоб розрядити обстановку.",
    "Емпатія + схожість: покажи, що ви схожі або що ти розумієш її стан.",
    "Загадка + інтрига: заінтригуй, щоб їй захотілося дізнатися більше.",
    "Впевненість + виклик: додай елемент виклику, але без агресії.",
    "Неочікуваність: зроби нестандартний комплімент, який виділиться.",
    "Соціальний доказ: натякни, що вона особлива, бо ти зазвичай таке не кажеш.",
    "Грайливість + метафора: використай цікаву метафору, пов'язану з моментом."
]

SIZE_CATEGORY = {
    "0": "small", "1": "small", "1.5": "small",
    "2": "medium", "2.5": "medium", "3": "medium", "3.5": "medium",
    "4": "large", "4.5": "large", "5": "large", "5+": "large",
}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("0", callback_data="0"),
         InlineKeyboardButton("1", callback_data="1"),
         InlineKeyboardButton("1.5", callback_data="1.5")],
        [InlineKeyboardButton("2", callback_data="2"),
         InlineKeyboardButton("2.5", callback_data="2.5"),
         InlineKeyboardButton("3", callback_data="3")],
        [InlineKeyboardButton("3.5", callback_data="3.5"),
         InlineKeyboardButton("4", callback_data="4"),
         InlineKeyboardButton("4.5", callback_data="4.5")],
        [InlineKeyboardButton("5", callback_data="5"),
         InlineKeyboardButton("5+", callback_data="5+")],
    ]
    await update.message.reply_text(
        "🎯 **Психологічний підкат**\n\n"
        "Обери приблизний розмір грудей дівчини, до якої хочеш підкатити.\n"
        "Я використаю **випадкову психологічну тактику** (гумор, комплімент, загадку тощо), "
        "щоб створити короткий, але ефективний підкат, який її зачепить.",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

async def generate_pickup(size: str, category: str) -> str:
    tactic = random.choice(TACTICS)
    
    tone = {
        "small": "ніжний, романтичний",
        "medium": "грайливий, дотепний",
        "large": "впевнений, трохи зухвалий"
    }.get(category, "нейтральний")

    prompt = (
        f"Ти — експерт з пікапу та психології. Напиши ОДНЕ коротке речення (до 15 слів) — підкат українською мовою "
        f"для знайомства з дівчиною, яка має приблизно {size} розмір грудей. "
        f"Тональність: {tone}. Використай психологічну тактику: {tactic}. "
        f"Не згадуй розмір грудей у самому підкаті. Тільки фраза, без пояснень."
    )

    url = f"https://api.cloudflare.com/client/v4/accounts/{CLOUDFLARE_ACCOUNT_ID}/ai/run/{MODEL}"
    headers = {
        "Authorization": f"Bearer {CLOUDFLARE_API_TOKEN}",
        "Content-Type": "application/json"
    }
    data = {
        "messages": [{"role": "user", "content": prompt}]
    }

    try:
        response = requests.post(url, headers=headers, json=data, timeout=30)
        response.raise_for_status()
        result = response.json()
        if result.get("success"):
            answer = result["result"]["response"]
            return answer.strip()
        else:
            errors = result.get("errors", [])
            return f"❌ Помилка Cloudflare: {errors}"
    except Exception as e:
        logging.error(f"Cloudflare AI error: {e}")
        return f"❌ Помилка: {str(e)}"

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    size = query.data
    category = SIZE_CATEGORY[size]

    await query.edit_message_text("🧠 Обираю психологічну тактику... секунду...")

    line = await generate_pickup(size, category)

    await context.bot.send_message(
        chat_id=query.message.chat_id,
        text=f"📏 **Розмір (приблизно):** {size}\n\n💬 **Підкат:**\n{line}\n\n🔄 /start ще раз",
        parse_mode='Markdown'
    )

def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))

    print("🚀 Бот з психологічними тактиками запущено!")
    app.run_polling()

if __name__ == "__main__":
    main()
