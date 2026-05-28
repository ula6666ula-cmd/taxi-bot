import telebot
from telebot import types
import json
import os
import re

TOKEN = "8594048221:AAFYSCHGT1GDPydisGWvzj5Z4jSQeKUs06c"
GROUP_ID = -1003875819316
ADMIN_ID = 1794307964
CARD = "9860600409265755"

bot = telebot.TeleBot(TOKEN)

BALANCE_FILE = "balances.json"
DRIVERS_FILE = "drivers.json"
STATS_FILE = "stats.json"

# ================= FILES =================
def load_data(file):
    if os.path.exists(file):
        try:
            with open(file, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_data(file, data):
    with open(file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)

user_balance = load_data(BALANCE_FILE)
drivers = load_data(DRIVERS_FILE)
stats = load_data(STATS_FILE)

orders = {}
step_data = {}
payment_wait = {}
register_step = {}

def save_all():
    save_data(BALANCE_FILE, user_balance)
    save_data(DRIVERS_FILE, drivers)
    save_data(STATS_FILE, stats)

# ================= MENU =================
def menu():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("🚕 Заказ бериш")
    kb.add("🚖 Хайдовчи бўлиш", "💰 Баланс")
    kb.add("📊 Статистика", "❌ Бекор қилиш")
    return kb

def cancel(msg):
    uid = msg.chat.id
    step_data.pop(uid, None)
    register_step.pop(uid, None)
    payment_wait.pop(uid, None)
    bot.send_message(uid, "❌ Бекор қилинди", reply_markup=menu())

# ================= START =================
@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "Ассалому алайкум 👋", reply_markup=menu())

# ================= CANCEL =================
@bot.message_handler(func=lambda m: m.text == "❌ Бекор қилиш")
def cancel_handler(message):
    cancel(message)

# ================= DRIVER REGISTER =================
@bot.message_handler(func=lambda m: m.text == "🚖 Хайдовчи бўлиш")
def become_driver(message):
    uid = str(message.chat.id)

    if uid in drivers:
        bot.send_message(message.chat.id, "✅ Сиз рўйхатдан ўтгансиз")
        return

    register_step[message.chat.id] = {"step": "name"}
    bot.send_message(message.chat.id, "👤 Исмингизни киритинг")

@bot.message_handler(func=lambda m: m.chat.id in register_step)
def register_driver(message):
    uid = str(message.chat.id)
    data = register_step[message.chat.id]

    if data["step"] == "name":
        data["name"] = message.text
        data["step"] = "phone"
        bot.send_message(message.chat.id, "📞 +998XXXXXXXXX форматда номер киритинг")
        return

    if data["step"] == "phone":
        if not re.fullmatch(r"\+998\d{9}", message.text):
            bot.send_message(message.chat.id, "❌ Нотўғри формат\nМисол: +998901234567")
            return

        drivers[uid] = {
            "name": data["name"],
            "phone": message.text
        }

        user_balance[uid] = 0
        stats[uid] = {"orders": 0, "spent": 0}
        save_all()

        del register_step[message.chat.id]

        bot.send_message(message.chat.id, "✅ Рўйхатдан ўтдингиз", reply_markup=menu())

# ================= BALANCE =================
@bot.message_handler(func=lambda m: m.text == "💰 Баланс")
def balance(message):
    uid = str(message.chat.id)

    if uid not in drivers:
        bot.send_message(message.chat.id, "❌ Аввал рўйхатдан ўтинг")
        return

    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("💳 Чек юбориш", callback_data="send_check"))

    bot.send_message(
        message.chat.id,
        f"💰 Баланс: {user_balance.get(uid,0)} сўм\n\n💳 Карта:\n{CARD}",
        reply_markup=kb
    )

# ================= CHECK =================
@bot.callback_query_handler(func=lambda c: c.data == "send_check")
def send_check(c):
    payment_wait[c.from_user.id] = True
    bot.send_message(c.from_user.id, "📸 Чек расмини юборинг")

@bot.message_handler(content_types=['photo'])
def receive_check(message):
    uid = message.chat.id

    if uid not in payment_wait:
        return

    bot.forward_message(ADMIN_ID, uid, message.message_id)
    bot.send_message(ADMIN_ID, f"/pay {uid} 5000")
    bot.send_message(uid, "✅ Админга юборилди")

    del payment_wait[uid]

# ================= ORDER =================
@bot.message_handler(func=lambda m: m.text == "🚕 Заказ бериш")
def order_start(message):
    step_data[message.chat.id] = {"step": "from"}
    bot.send_message(message.chat.id, "📍 Қаердан йулга чикасиз?")

@bot.message_handler(func=lambda m: m.chat.id in step_data)
def process_order(message):
    uid = message.chat.id
    data = step_data[uid]

    if data["step"] == "from":
        data["from"] = message.text
        data["step"] = "to"
        bot.send_message(uid, "📍 Қаерга борасиз?")
        return

    if data["step"] == "to":
        data["to"] = message.text
        data["step"] = "seat"
        bot.send_message(uid, "👥 Нечта жой?")
        return

    if data["step"] == "seat":
        if not message.text.isdigit():
            bot.send_message(uid, "❌ Фақат сон")
            return
        data["seat"] = message.text
        data["step"] = "phone"
        bot.send_message(uid, "📞 Телефон?")
        return

    if data["step"] == "phone":
        data["phone"] = message.text
        data["step"] = "time"
        bot.send_message(uid, "⏰ Вақт?")
        return

    if data["step"] == "time":
        data["time"] = message.text
        data["step"] = "comment"
        bot.send_message(uid, "📝 Изоҳ (йўқ бўлса -)")
        return

    if data["step"] == "comment":
        data["comment"] = message.text

        order_id = len(orders) + 1
        orders[order_id] = {"customer_id": uid, **data}

        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton("✅ Қабул қилиш", callback_data=f"accept_{order_id}"))

        txt = f"""
🚕 Янги заказ

📍 Қаердан: {data['from']}
📍 Қаерга: {data['to']}
👥 Жой: {data['seat']}
📞 {data['phone']}
⏰ {data['time']}
📝 {data['comment']}
"""

        bot.send_message(GROUP_ID, txt, reply_markup=kb)
        bot.send_message(uid, "✅ Заказ юборилди", reply_markup=menu())

        del step_data[uid]

# ================= ACCEPT =================
@bot.callback_query_handler(func=lambda c: c.data.startswith("accept_"))
def accept_order(c):
    order_id = int(c.data.split("_")[1])

    if order_id not in orders:
        bot.answer_callback_query(c.id, "Эски заказ")
        return

    uid = str(c.from_user.id)

    if uid not in drivers:
        bot.send_message(c.from_user.id, "❌ Аввал рўйхатдан ўтинг")
        return

    if user_balance.get(uid, 0) < 5000:
        bot.send_message(c.from_user.id, "❌ Баланс етарли эмас")
        return

    user_balance[uid] -= 5000
    stats[uid]["orders"] += 1
    stats[uid]["spent"] += 5000
    save_all()

    driver = drivers[uid]
    customer_id = orders[order_id]["customer_id"]

    bot.edit_message_text(
        f"✅ {driver['name']} қабул қилди",
        c.message.chat.id,
        c.message.message_id
    )

    bot.send_message(
        customer_id,
        f"🚖 Ҳайдовчи:\n👤 {driver['name']}\n📞 {driver['phone']}"
    )

    del orders[order_id]

# ================= STATS =================
@bot.message_handler(func=lambda m: m.text == "📊 Статистика")
def stat(message):
    uid = str(message.chat.id)

    if uid not in stats:
        bot.send_message(message.chat.id, "❌ Йўқ")
        return

    s = stats[uid]

    bot.send_message(
        message.chat.id,
        f"""
📊 Статистика

🚕 Заказ: {s['orders']}
💸 Сарф: {s['spent']}
💰 Баланс: {user_balance.get(uid,0)}
"""
    )

# ================= ADMIN PAY =================
@bot.message_handler(commands=['pay'])
def pay(message):
    if message.from_user.id != ADMIN_ID:
        return

    try:
        _, uid, amount = message.text.split()
        amount = int(amount)

        user_balance[uid] = user_balance.get(uid, 0) + amount
        save_all()

        bot.send_message(int(uid), f"✅ {amount} сўм тушди")
        bot.reply_to(message, "✅")

    except:
        bot.reply_to(message, "❌ /pay user_id amount")

print("Bot ishga tushdi...")
bot.infinity_polling()
