import telebot
from telebot import types
import json
import os

TOKEN = "8594048221:AAFYSCHGT1GDPydisGWvzj5Z4jSQeKUs06c"
GROUP_ID = -1003875819316
ADMIN_ID = 1794307964
CARD = "9860600409265755"

bot = telebot.TeleBot(TOKEN)

BALANCE_FILE = "balances.json"
DRIVERS_FILE = "drivers.json"

def load_json(file):
    if os.path.exists(file):
        with open(file, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_json(file, data):
    with open(file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)

balances = load_json(BALANCE_FILE)
drivers = load_json(DRIVERS_FILE)

orders = {}
register_step = {}
order_step = {}
payment_wait = {}


def save_balances():
    save_json(BALANCE_FILE, balances)

def save_drivers():
    save_json(DRIVERS_FILE, drivers)


def menu():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("🚕 Заказ бериш")
    kb.add("🚖 Хайдовчи бўлиш", "💰 Хайдовчи Баланси")
    return kb


@bot.message_handler(commands=['start'])
def start(message):
    uid = str(message.chat.id)

    if uid not in balances:
        balances[uid] = 0
        save_balances()

    bot.send_message(
        message.chat.id,
        "Ассалому алайкум 👋",
        reply_markup=menu()
    )


# ===== DRIVER REGISTER =====
@bot.message_handler(func=lambda m: m.text == "🚖 Хайдовчи бўлиш")
def become_driver(message):
    uid = str(message.chat.id)

    if uid in drivers:
        bot.send_message(message.chat.id, "✅ Сиз аллақачон рўйхатдан ўтгансиз")
        return

    register_step[message.chat.id] = "name"
    bot.send_message(message.chat.id, "👤 Исмингизни киритинг")


# ===== ORDER =====
@bot.message_handler(func=lambda m: m.text == "🚕 Заказ бериш")
def new_order(message):
    order_step[message.chat.id] = {"step": "from"}
    bot.send_message(message.chat.id, "📍 Қаердан йўлга чиқасиз?")


@bot.message_handler(func=lambda m: m.chat.id in register_step)
def register_driver(message):
    uid = str(message.chat.id)

    if register_step[message.chat.id] == "name":
        drivers[uid] = {"name": message.text}
        register_step[message.chat.id] = "phone"
        bot.send_message(message.chat.id, "📞 Телефон рақамингизни киритинг")
        return

    elif register_step[message.chat.id] == "phone":
        drivers[uid]["phone"] = message.text
        register_step[message.chat.id] = "car"
        bot.send_message(message.chat.id, "🚘 Машина маркасини киритинг")
        return

    elif register_step[message.chat.id] == "car":
        drivers[uid]["car"] = message.text
        save_drivers()
        del register_step[message.chat.id]

        bot.send_message(
            message.chat.id,
            "✅ Сиз хайдовчи сифатида рўйхатдан ўтдингиз",
            reply_markup=menu()
        )


@bot.message_handler(func=lambda m: m.chat.id in order_step)
def process_order(message):
    uid = message.chat.id
    data = order_step[uid]

    if data["step"] == "from":
        data["from"] = message.text
        data["step"] = "to"
        bot.send_message(uid, "📍 Қаерга борасиз?")

    elif data["step"] == "to":
        data["to"] = message.text
        data["step"] = "seat"
        bot.send_message(uid, "👥 Нечта жой банд киласиз?")

    elif data["step"] == "seat":
        data["seat"] = message.text
        data["step"] = "phone"
        bot.send_message(uid, "📞 Телефон номер?")

    elif data["step"] == "phone":
        data["phone"] = message.text

        order_id = len(orders) + 1
        orders[order_id] = {"customer_id": uid, **data.copy()}

        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton(
            "✅ Қабул қилиш",
            callback_data=f"accept_{order_id}"
        ))

        bot.send_message(
            GROUP_ID,
            f"🚕 Янги заказ\n\n"
            f"📍 Қаердан: {data['from']}\n"
            f"📍 Қаерга: {data['to']}\n"
            f"👥 Жой: {data['seat']}\n"
            f"📞 {data['phone']}",
            reply_markup=kb
        )

        bot.send_message(uid, "✅ Заказ юборилди", reply_markup=menu())
        del order_step[uid]


# ===== BALANCE =====
@bot.message_handler(func=lambda m: m.text == "💰 Хайдовчи Баланси")
def balance(message):
    uid = str(message.chat.id)

    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton(
        "💳 Баланс тўлдириш",
        callback_data="pay"
    ))

    bot.send_message(
        message.chat.id,
        f"💰 Баланс: {balances.get(uid,0)} сўм\n\n💳 Карта:\n{CARD}",
        reply_markup=kb
    )


@bot.callback_query_handler(func=lambda c: c.data == "pay")
def pay_request(call):
    payment_wait[call.from_user.id] = True
    bot.send_message(call.from_user.id, "📸 Чек расмини юборинг")


@bot.message_handler(content_types=['photo'])
def receive_check(message):
    uid = message.chat.id

    if uid not in payment_wait:
        return

    bot.forward_message(ADMIN_ID, uid, message.message_id)

    bot.send_message(
        ADMIN_ID,
        f"/pay {uid} 5000"
    )

    bot.send_message(uid, "✅ Чек админга юборилди")
    del payment_wait[uid]


# ===== ADMIN =====
@bot.message_handler(commands=['pay'])
def admin_pay(message):
    if message.from_user.id != ADMIN_ID:
        return

    try:
        _, uid, amount = message.text.split()

        balances[uid] = balances.get(uid, 0) + int(amount)
        save_balances()

        bot.send_message(int(uid), f"✅ Баланс {amount} сўмга тўлдирилди")
        bot.reply_to(message, "✅ Тасдиқланди")

    except:
        bot.reply_to(message, "❌ /pay user_id amount")


# ===== ACCEPT ORDER =====
@bot.callback_query_handler(func=lambda c: c.data.startswith("accept_"))
def accept_order(call):
    order_id = int(call.data.split("_")[1])

    if order_id not in orders:
        return

    uid = str(call.from_user.id)

    if uid not in drivers:
        bot.send_message(call.from_user.id, "❌ Аввал рўйхатдан ўтинг")
        return

    if balances.get(uid, 0) < 5000:
        bot.send_message(call.from_user.id, "❌ Баланс етарли эмас")
        return

    balances[uid] -= 5000
    save_balances()

    data = orders[order_id]
    customer_id = data["customer_id"]

    bot.edit_message_text(
        f"✅ {drivers[uid]['name']} заказни қабул қилди",
        call.message.chat.id,
        call.message.message_id
    )

    # driver
    bot.send_message(
        int(uid),
        f"✅ Заказ қабул қилинди\n\n"
        f"📞 {data['phone']}\n"
        f"📍 Қаердан: {data['from']}\n"
        f"📍 Қаерга: {data['to']}\n"
        f"👥 Жой: {data['seat']}\n\n"
        f"💰 Қолдиқ: {balances[uid]} сўм"
    )

    # client
    bot.send_message(
        customer_id,
        f"✅ Заказ қабул қилинди\n\n"
        f"👤 Ҳайдовчи: {drivers[uid]['name']}\n"
        f"📞 {drivers[uid]['phone']}\n"
        f"🚘 Машина: {drivers[uid]['car']}"
    )

    del orders[order_id]


print("Bot ishga tushdi...")
bot.infinity_polling()
