import telebot
from telebot import types
import os
os.environ["DJANGO_SETTINGS_MODULE"] = "bet.settings"
import django
django.setup()
from django.contrib.auth.models import User
from main.models import Profile
from django.core.files import File
from urllib.request import urlopen
from tempfile import NamedTemporaryFile



API_TOKEN = "6346891549:AAEY4mP5lsg4dB4xEpJgXaQ9hw3VykC4usY"
bot = telebot.TeleBot(API_TOKEN)

def extract_referral_id(message):
    # Extracts the unique_code from the sent /start command.
    return message.split()[1] if len(message.split()) > 1 else 'admin'

def is_user(message):
    try:
        user = User.objects.get(username=message.from_user.id)
    except User.DoesNotExist:
        user = User.objects.create_user(
            username=message.from_user.id, password=str(message.from_user.id)
        )
    
    return user



@bot.message_handler(commands=['start'])
def send_welcome(message):
    user=is_user(message)
    if user.last_login:
        keyboard = telebot.types.InlineKeyboardMarkup()
        keyboard.row(
            telebot.types.InlineKeyboardButton("Open App", web_app=types.WebAppInfo('https://new-folder-production.up.railway.app/'))
        )
        message = bot.send_message(
            message.chat.id,
            f"Welcome back",
            reply_markup=keyboard,
        )
    else:
        
        referee=Profile.objects.get(referral_id=extract_referral_id(message.text)).user
        user.profile.referee=referee
        markup=types.ReplyKeyboardMarkup(row_width=1)
        markup.add(types.KeyboardButton('Register',request_contact=True))
        bot.send_message(message.chat.id,"You don't seem to have an account \n click to register",reply_markup=markup)


@bot.message_handler(content_types=['contact'])
def get_number(message):
    user=is_user(message)
    if user.last_login:
        user.profile.phone=message.contact.phone_number
    else:
        data=bot.get_user_profile_photos(message.from_user.id)

        if data.total_count > 0:
            file=bot.get_file(data.photos[0][1].file_id)
            url=f'https://api.telegram.org/file/bot{API_TOKEN}/{file.file_path}'
            img_temp = NamedTemporaryFile(delete=True)
            img_temp.write(urlopen(url).read())
            img_temp.flush()
            user.profile.image.save(f"image_{user.pk}", File(img_temp))
            user.profile.phone=message.contact.phone_number

        user.save()
    return user




bot.infinity_polling()