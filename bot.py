from datetime import datetime
import time
import phonenumbers 
from phonenumbers import geocoder 
import pytz
import telebot
from telebot import types
import os

os.environ["DJANGO_SETTINGS_MODULE"] = "bet.settings"
import django

django.setup()

from djmoney.money import Money
from django.urls import reverse
from binance.client import Client
import pycountry
from djmoney.contrib.exchange.models import convert_money
from babel.numbers import get_territory_currencies
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from django.contrib.auth.models import User
from main.models import EtherTransaction, Profile
from django.core.files import File
from urllib.request import urlopen
from tempfile import NamedTemporaryFile

from dotenv import load_dotenv,find_dotenv
import sys

load_dotenv(find_dotenv(sys.path[0]+'/main/.env'))

api_key = os.environ.get("API_KEY")
api_secret = os.environ.get("API_SECRET")
wldAddress = "0xbc0367e2fd8885ccfbb1032f3ceb7905378e8e5e"


API_TOKEN = os.environ.get("API_TOKEN")
bot = telebot.TeleBot(API_TOKEN)
def alert(id,message):
    bot.send_message(id, message)


def landing(message):
    user = is_user(message)
    keyboard = telebot.types.InlineKeyboardMarkup()
    keyboard.row(
        telebot.types.InlineKeyboardButton(
            "Open App",
            web_app=types.WebAppInfo("https://new-folder.onrender.com/"),
        )
    )
    keyboard.row(
        telebot.types.InlineKeyboardButton("⚙️ My Account", callback_data="account")
    )
    message = bot.send_message(
        message.chat.id,
        f"💰 Current balance: {user.profile.balance} \nSelect an Option?",
        reply_markup=keyboard,
    )


def extract_referral_id(message):
    # Extracts the unique_code from the sent /start command.
    return message.split()[1] if len(message.split()) > 1 else "admin"


def is_user(message):
    try:
        user = User.objects.get(username=message.from_user.username)

    except AttributeError:
        user = User.objects.get(username=message.message.chat.username)

    except User.DoesNotExist:
        user = User.objects.create_user(
            username=message.from_user.username,
            password=str(message.from_user.username),
        )

    return user


@bot.message_handler(commands=["start"])
def send_welcome(message):
    user = is_user(message)
    if user.last_login:
        message = bot.send_message(message.chat.id, f"Welcome back {user.username}")
        landing(message)

    else:
        referee = Profile.objects.get(
            referral_id=extract_referral_id(message.text)
        ).user
        user.profile.referee = referee
        markup = types.ReplyKeyboardMarkup(row_width=1)
        markup.add(types.KeyboardButton("Register", request_contact=True))
        bot.send_message(
            message.chat.id,
            "You don't seem to have an account \n click keyboard below to register",
            reply_markup=markup,
        )


@bot.message_handler(func=lambda message: True)
def echo(message):
    user = is_user(message)
    replied_to = message.reply_to_message.text
    if replied_to == "Enter transaction hash:":
        count = 0
        bot.send_message(message.chat.id, "processing...")
        while count < 5:
            t = EtherTransaction.objects.filter(hash=message.text)
            count += 1
            time.sleep(5 + count)
            if t.count() == 0:
                continue
            else:
                tx = t[0]
                if tx.redeemed == False:
                    tx.redeemed = True
                    user.profile.deposit(amount=tx.value)  # safe input?
                    tx.save()
                    bot.send_message(
                        message.chat.id, f"Successfully deposited WLD {tx.value}"
                    )
                    return
                else:
                    bot.send_message(
                        message.chat.id,
                        f"Transaction has already been credited",
                    )
                    markup = types.ForceReply(selective=False)
                    bot.send_message(
                        message.chat.id, f"Enter transaction hash:", reply_markup=markup
                    )
                    return
        bot.send_message(
            message.chat.id,
            f"Transaction has not reflected, please try again",
        )
        markup = types.ForceReply(selective=False)
        bot.send_message(
            message.chat.id, f"Enter transaction hash:", reply_markup=markup
        )

    if replied_to == "Enter Your Worldcoin address:":
        user.profile.address = message.text
        user.save()
        bot.send_message(message.chat.id, f"address set to {message.text} \n")
        keyboard = telebot.types.InlineKeyboardMarkup()
        markup = types.ForceReply(selective=False)
        bot.send_message(
            message.chat.id,
            f"Enter withdraw amount: max {user.profile.balance}",
            reply_markup=markup,
        )
    if replied_to == "Enter New Worldcoin address:":
        user.profile.address = message.text
        user.save()
        bot.send_message(message.chat.id, f"address set to {message.text} \n")
        landing(message)

    if replied_to.startswith("Enter withdraw amount:"):
        amount = message.text
        if user.profile.balance >= Money(amount, "WLD"):
            if user.profile.has_withdrawn():
                spot_client = Client(api_key, api_secret)
                try:
                    spot_client.withdraw(
                        coin="WLD", amount=amount, address=address, recvWindow=6000
                    )
                    bot.send_message(message.chat.id, "Withdrawal Initiated")

                except Exception as e:
                    print(e)
                    bot.send_message(
                        message.chat.id,
                        "Failed, please try again later or contact admin",
                    )

            else:
                sender = os.environ.get("sender")
                receiver = os.environ.get("receiver")
                subject = amount
                url = reverse(
                    "main:withdraw", kwargs={"user_id": user.id, "amount": amount}
                )
                message = f"{user.profile.address},\n \n \n \n {url}"

                smtp_server = "smtp.gmail.com"
                smtp_port = 465
                username = sender
                password = os.environ.get("PASSWORD")

                msg = MIMEMultipart()
                msg["From"] = sender
                msg["To"] = receiver
                msg["Subject"] = subject

                msg.attach(MIMEText(message, "plain"))

                context = ssl.create_default_context()

                try:
                    with smtplib.SMTP_SSL(
                        smtp_server, smtp_port, context=context
                    ) as smtp:
                        smtp.login(username, password)

                        # Send the email
                        smtp.send_message(msg)
                        bot.send_message(message.chat.id, "Withdrawal Initiated")

                except Exception as e:
                    print(f"Error: {e}")
                    bot.send_message(
                        message.chat.id,
                        "Failed, please try again later or contact admin",
                    )
        else:
            bot.send_message(message.chat.id, "insufficient balance")

    if replied_to.startswith("Enter country short code eg. USA:"):
        input = str(message.text)
        try:
            cntry = pycountry.countries.lookup(input)
            keyboard = telebot.types.InlineKeyboardMarkup()
            keyboard.row(
                telebot.types.InlineKeyboardButton(
                    f"{cntry.name} {cntry.flag}",
                    callback_data=f"unicode-{cntry.alpha_3}",
                )
            )
            bot.send_message(message.chat.id, "Select match:", reply_markup=keyboard)
        except LookupError:
            markup = types.ForceReply(selective=False)
            bot.send_message(message.chat.id, "Invalid try again")
            bot.send_message(
                message.chat.id,
                "Enter country short code eg. USA:",
                reply_markup=markup,
            )

    if replied_to.startswith("Enter number to redeem:"):
        ref = Profile.objects.filter(referee=user)
        val = ref.filter(is_valid=True)
        num = int(message.text)
        if num > 4 and num <= (val.count() - user.profile.redeem):
            user.profile.redeem += num
            cred = Money(0.2 * num, "WLD")
            user.profile.credit(cred.amount)
            user.save()
            keyboard = telebot.types.InlineKeyboardMarkup()
            keyboard.row(
                telebot.types.InlineKeyboardButton("back to home", callback_data="home")
            )

            bot.reply_to(
                message,
                f"Successfully redeemed {cred} \nNew balance: {user.profile.balance}",
                reply_markup=keyboard,
            )

        else:
            markup=types.ForceReply(selective=False)
            bot.send_message(
                message.chat.id, "Invalid amount, try again"
            )
            bot.send_message(
            message.chat.id,
            f"Enter number to redeem: \n Minimum: 5",
            reply_markup=markup,
        )


@bot.message_handler(content_types=["contact"])
def get_number(message):
    user = is_user(message)
    if user.last_login:
        user.profile.phone = message.contact.phone_number
    else:
        data = bot.get_user_profile_photos(message.from_user.id)

        if data.total_count > 0:
            file = bot.get_file(data.photos[0][1].file_id)
            url = f"https://api.telegram.org/file/bot{API_TOKEN}/{file.file_path}"
            img_temp = NamedTemporaryFile(delete=True)
            img_temp.write(urlopen(url).read())
            img_temp.flush()
            user.profile.image.save(f"image_{user.pk}", File(img_temp))
        phone=message.contact.phone_number
        user.profile.phone = phone
        user.last_login = datetime.now(pytz.utc)
       
        pn = phonenumbers.parse(f'+{phone}') 
        
        country = pycountry.countries.search_fuzzy(geocoder.description_for_number(pn, "en"))
        user.profile.country=country[0].alpha_3
        user.profile.chat_id=message.chat.id
        user.save()
    markup=types.ReplyKeyboardRemove()
    message = bot.send_message(message.chat.id, f"Welcome to Telebets {user.username}!", reply_markup=markup)
    landing(message)


@bot.callback_query_handler(func=lambda call: True)
def answer_callback(query):
    user = is_user(query)
    data = query.data
    if data.startswith("account"):
        keyboard = telebot.types.InlineKeyboardMarkup()
        keyboard.row(
            telebot.types.InlineKeyboardButton("⬆️ Deposit", callback_data="deposit")
        )
        keyboard.row(
            telebot.types.InlineKeyboardButton("⬇️ Withdraw", callback_data="withdraw")
        )
        keyboard.row(
            telebot.types.InlineKeyboardButton("⚙️ Settings", callback_data="settings")
        )
        bot.send_message(query.message.chat.id, "My Account:", reply_markup=keyboard)

    if data.startswith("withdraw"):
        address = user.profile.address
        if address:
            bot.send_message(query.message.chat.id, f"Current address is {address} \n")
            keyboard = telebot.types.InlineKeyboardMarkup()
            markup = types.ForceReply(selective=False)
            bot.send_message(
                query.message.chat.id,
                f"Enter withdraw amount: max {user.profile.balance}",
                reply_markup=markup,
            )
        else:
            markup = types.ForceReply(selective=False)
            bot.send_message(
                query.message.chat.id, "Enter Worldcoin address:", reply_markup=markup
            )

    if data.startswith("deposit"):
        bot.send_message(
            query.message.chat.id,
            f"Send Worldcoin to this address \n `{wldAddress}`",
            parse_mode="MarkdownV2",
        )
        markup = types.ForceReply(selective=False)
        bot.send_message(
            query.message.chat.id, f"Enter transaction hash:", reply_markup=markup
        )

    if data.startswith("settings"):
        keyboard = telebot.types.InlineKeyboardMarkup()
        keyboard.row(
            telebot.types.InlineKeyboardButton(
                f"country: {user.profile.country.unicode_flag}", callback_data="country"
            )
        )
        keyboard.row(
            telebot.types.InlineKeyboardButton(
                "Withdraw address", callback_data="address"
            )
        )
        keyboard.row(
            telebot.types.InlineKeyboardButton("👥 Referrals", callback_data="referrals")
        )
        bot.send_message(query.message.chat.id, "settings", reply_markup=keyboard)

    if data.startswith("address"):
        markup = types.ForceReply(selective=False)
        bot.send_message(
            query.message.chat.id, "Enter New Worldcoin address:", reply_markup=markup
        )

    if data.startswith("country"):
        markup = types.ForceReply(selective=False)
        bot.send_message(
            query.message.chat.id,
            "Enter country short code eg. USA:",
            reply_markup=markup,
        )

    if data.startswith("unicode"):
        country = data.split("-")[1]
        user.profile.country = country
        currency = get_territory_currencies(user.profile.country.code)[0]
        user.save()
        bot.answer_callback_query(query.id, "successfully changed")
        landing(query.message)

    if data.startswith("referrals"):
        keyboard = telebot.types.InlineKeyboardMarkup()
        ref = Profile.objects.filter(referee=user)
        val = ref.filter(is_valid=True)
        keyboard.row(
            telebot.types.InlineKeyboardButton("redeem", callback_data="redeem")
        )
        bot.send_message(
            query.message.chat.id,
            f"Share link: https://t.me/surebet_bot?start={user.profile.referral_id} \n Total referrals: {ref.count()} \n Valid referrals: {val.count()} \n Redeemed: {user.profile.redeem} \n Available for redemption: {val.count()-user.profile.redeem}",
            reply_markup=keyboard,
        )

    if data.startswith("redeem"):
        markup = types.ForceReply(selective=False)
        ref = Profile.objects.filter(referee=user)
        val = ref.filter(is_valid=True)
        num = val.count() - user.profile.redeem
        currency = get_territory_currencies(user.profile.country.code)[0]
        cred = convert_money(Money(50 * num, "KES"), currency)

        bot.send_message(
            query.message.chat.id, f"Available for redemption: {num} ≈ {cred}"
        )
        bot.send_message(
            query.message.chat.id,
            f"Enter number to redeem: \n Minimum: 5",
            reply_markup=markup,
        )


bot.infinity_polling()
