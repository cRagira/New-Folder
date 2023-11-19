import base64
import json
import telebot
from telebot import types
import os
import django
os.environ["DJANGO_SETTINGS_MODULE"] = "bet.settings"
django.setup()
from django.contrib.auth.models import User

API_TOKEN="6339155566:AAFxn0uwyuTODtdsvoeNPkPWVdV23FYmohI"
bot=telebot.TeleBot(API_TOKEN)



def get_user(message):
    try:
        user = User.objects.get(username=message.chat.username)
    except AttributeError:
        user = User.objects.get(username=message.message.chat.username)
    except User.DoesNotExist:
        user = User.objects.create(
            username=message.chat.username, password=message.chat.id
        )
        user.save()
    return user

def extract_params(message):
    # Extracts the params from the sent /start command.
    return message.split() if len(message.split()) > 1 else None

def home(message, user):
    keyboard = telebot.types.InlineKeyboardMarkup()
    keyboard.row(
        telebot.types.InlineKeyboardButton("send", callback_data="games")
    )
    keyboard.row(
        telebot.types.InlineKeyboardButton("receive", callback_data="account")
    )
    keyboard.row(
        telebot.types.InlineKeyboardButton("withdraw", callback_data="account")
    )
    keyboard.row(
        telebot.types.InlineKeyboardButton("deposit", callback_data="account")
    )
    message = bot.send_message(
        message.chat.id,
        f"💰 Current balance: {user.profile.balance}",
        reply_markup=keyboard,
    )

@bot.message_handler(commands=["start"])
def handle_message(message):
    params64=extract_params(message.text)
    if params64 != None:
        params64b=params64.encode("ascii")
        params=base64.b64decode(params64b).decode("ascii")
        params=json.loads(params)
        if params['command']=="send":
            recepient = params.recepient
            amount = params.amount
            markup = types.ForceReply(selective=False)
            bot.send_message(message.chat.id, f' To send {amount} to {recepient}, enter capcha', reply_markup=markup)
        if params['command']=="withdraw":
            pass
    else:
        user = get_user(message)
        bot.reply_to(message, f"Hello {message.chat.username}")
        home(message, user)

@bot.callback_query_handler(func=lambda call: True)
def iq_callback(query):
    user = get_user(query)
    data=query.data
    if data.startswith("deposit"):
        pass

    if data.startswith("withdraw"):
        pass

    if data.startswith("send"):
        pass

    if data.startswith("account"):
        pass
bot.infinity_polling()

