import base64
import time
import babel
from babel.numbers import get_territory_currencies
import django
import os

os.environ["DJANGO_SETTINGS_MODULE"] = "bet.settings"
django.setup()
from pprint import pprint
import telebot
from telebot import types
from main.models import Match, BetTicket, BetTicketSelection, Profile, get_currency
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from djmoney.money import Money
from djmoney.contrib.exchange.models import convert_money
import pycountry


API_TOKEN = "6346891549:AAEY4mP5lsg4dB4xEpJgXaQ9hw3VykC4usY"
bot = telebot.TeleBot(API_TOKEN)
betslip = []
min_bet = 100
def update_exchange():
    from djmoney.contrib.exchange.backends import FixerBackend
    print('updating exchange')
    FixerBackend().update_rates()

def extract_referral_id(message):
    # Extracts the unique_code from the sent /start command.
    return message.split()[1] if len(message.split()) > 1 else None

def get_user(message):
    try:
        user = User.objects.get(username=message.chat.username)
    except AttributeError:
        user = User.objects.get(username=message.message.chat.username)
    except User.DoesNotExist:
        user = User.objects.create(
            username=message.chat.username, password=message.chat.id
        )
        referee=Profile.objects.get(referral_id=extract_referral_id(message.text)).user
        print(referee)
        user.profile.referee=referee

        user.save()
    return user


def get_betslip():
    total_odds = 1
    for item in betslip:
        total_odds *= float(item["odd"])
        total_odds = float("{:.2f}".format(total_odds))
    if total_odds > 1:
        return f"betslip({len(betslip)}): {total_odds}"
    return f"betslip(0)"


def show_games(message, page):
    global last
    games = Match.objects.all().filter(stage="sche").order_by("created")
    paginator = Paginator(games, 5)
    x = 0
    page_obj = paginator.get_page(page)  # page_number
    for match in page_obj:
        keyboard = telebot.types.InlineKeyboardMarkup()
        x += 1
        keyboard.row(
            telebot.types.InlineKeyboardButton(
                f"{match.home_odds}",
                callback_data=f"odd/{match.match_id}/1/{match.home_odds}",
            ),
            telebot.types.InlineKeyboardButton(
                f"{match.draw_odds}",
                callback_data=f"odd/{match.match_id}/x/{match.draw_odds}",
            ),
            telebot.types.InlineKeyboardButton(
                f"{match.away_odds}",
                callback_data=f"odd/{match.match_id}/2/{match.away_odds}",
            ),
        )
        if x % 5 == 0:
            keyboard.row(
                telebot.types.InlineKeyboardButton(
                    "➕ show more", callback_data=f"games_show_more{page}"
                )
            )
            keyboard.row(
                telebot.types.InlineKeyboardButton(
                    f"🧾 {get_betslip()}", callback_data="show_betslip"
                )
            )

        last = bot.send_message(message.chat.id, match, reply_markup=keyboard)

def show_tickets(message, page):
    user=get_user(message)
    tickets=BetTicket.objects.filter(user=user)
    paginator = Paginator(tickets, 5)
    x = 0
    page_obj = paginator.get_page(page)  # page_number
    for ticket in page_obj:
        keyboard = telebot.types.InlineKeyboardMarkup()
        x+=1
        keyboard.row(
            telebot.types.InlineKeyboardButton(ticket,callback_data=f"ticket-{ticket.id}")
            )
        if x % 5 == 0:
                keyboard.row(
                    telebot.types.InlineKeyboardButton(
                        "➕ show more", callback_data=f"ticket_show_more{page}"
                    )
                )


def home(message, user):
    keyboard = telebot.types.InlineKeyboardMarkup()
    keyboard.row(
        telebot.types.InlineKeyboardButton("⚽ Today Games", callback_data="games")
    )
    keyboard.row(
        telebot.types.InlineKeyboardButton("⚙️ My Account", callback_data="account")
    )
    message = bot.send_message(
        message.chat.id,
        f"💰 Current balance: {user.profile.balance} \nSelect an Option?",
        reply_markup=keyboard,
    )


@bot.message_handler(commands=["start"])
def send_welcome(message):
    user = get_user(message)
    bot.reply_to(message, f"Howdy {message.chat.username}")
    home(message, user)

@bot.message_handler(func=lambda message:True)
def handle_message(message):
    user = get_user(message)
    try:
        msg = message.json['reply_to_message']['text']
        if msg.startswith('Enter deposit amount'):
            deposit=str(message.json['text'])
            params="{'command':'send','recepient':bot_username,'amount':deposit}".encode("ascii")
            params64=base64.b64encode(params).decode("ascii")
            keyboard=telebot.types.InlineKeyboardMarkup()
            keyboard.row(
                    telebot.types.InlineKeyboardButton(
                        "Open Payza:", url=f"t.me/{bot_username}?start={params}"
                    )
            )
            bot.send_message(message.chat.id, 'deposit successfull',reply_markup=keyboard)

        elif msg.startswith('Enter withdraw amount'):
            draw=str(message.json['text'])
            #TODO call deposit function
            user.profile.debit(draw)
            user.save()
            keyboard=telebot.types.InlineKeyboardMarkup()
            keyboard.row(
                    telebot.types.InlineKeyboardButton(
                        "back to home", callback_data="home"
                    )
            )
            bot.reply_to(message, 'withdrawal initiated..',reply_markup=keyboard)

        elif msg.startswith('Enter number to redeem:'):
            ref=Profile.objects.filter(referee=user)
            val=ref.filter(is_valid=True)
            num=int(message.json['text'])
            if num>4 and num<=(val.count()-user.profile.redeem):
                user.profile.redeem+=num
                currency=get_territory_currencies(user.profile.country.code)[0]
                cred=convert_money(Money(50*num, "KES"),currency)
                user.profile.credit(cred.amount)
                user.save()
                keyboard=telebot.types.InlineKeyboardMarkup()
                keyboard.row(
                        telebot.types.InlineKeyboardButton(
                            "back to home", callback_data="home"
                        )
                )

                bot.reply_to(message, f'Successfully redeemed {cred} \nNew balance: {user.profile.balance}', reply_markup=keyboard)

            else:
                keyboard=telebot.types.InlineKeyboardMarkup()
                telebot.types.InlineKeyboardButton("redeem", callback_data='redeem')

                bot.send_message(message.chat.id, 'Invalid amount, try again', reply_markup=keyboard)

        elif msg.startswith('Enter country short code eg. USA:'):
            input=str(message.json['text'])
            try:
                cntry=pycountry.countries.lookup(input)
                keyboard=telebot.types.InlineKeyboardMarkup()
                keyboard.row(
                    telebot.types.InlineKeyboardButton(f'{cntry.name} {cntry.flag}', callback_data=f'unicode-{cntry.alpha_3}'))
                bot.send_message(message.chat.id, 'Select match:', reply_markup=keyboard)
            except LookupError:
                markup = types.ForceReply(selective=False)
                bot.send_message(message.chat.id, 'Invalid try again')
                bot.send_message(message.chat.id, 'Enter country short code eg. USA:', reply_markup=markup)



    


    except KeyError:
        pass


@bot.callback_query_handler(func=lambda call: True)
def iq_callback(query):
    user = get_user(query)
    data = query.data
    print(data)
    amount = min_bet
    if data.startswith("games"):
        page = 1
        if data == "games":
            show_games(query.message, page)
        elif data.startswith("games_show_more"):
            # print(query.json)
            keyboard = telebot.types.InlineKeyboardMarkup()
            # update markup by removing show betslip
            item = query.json["message"]["reply_markup"]["inline_keyboard"][:-2][0]
            keyboard.row(
                telebot.types.InlineKeyboardButton(
                    f'{item[0]["text"]}', callback_data=f'{item[0]["callback_data"]}'
                ),
                telebot.types.InlineKeyboardButton(
                    f'{item[1]["text"]}', callback_data=f'{item[1]["callback_data"]}'
                ),
                telebot.types.InlineKeyboardButton(
                    f'{item[2]["text"]}', callback_data=f'{item[2]["callback_data"]}'
                ),
            )
            bot.edit_message_reply_markup(
                query.message.chat.id, query.message.id, reply_markup=keyboard
            )
            page += int(data[-1:])
            show_games(query.message, page)

    if data.startswith("odd"):

        def search_dict(dict_list, key, value):
            # searches betslip dict  and returns index if selection  already exsts
            for i, item in enumerate(dict_list):
                if item[key] == value:
                    return i
            return -1

        cd = data.split("/")
        match = {
            "game_id": f"{cd[1]}",
            "selection": f"{cd[2]}",
            "odd": f"{cd[3]}",
        }  # selected event and odds
        index = search_dict(betslip, "game_id", f"{cd[1]}")
        if index >= 0:
            if betslip[index]["selection"] == cd[2]:
                del betslip[index]
                bot.answer_callback_query(query.id, "removed from betslip")
                return
            else:
                betslip[index]["selection"] = cd[2]
            bot.answer_callback_query(query.id, "betslip updated")
        betslip.append(match)
        bot.answer_callback_query(query.id, "added to betslip")
        # last_reply_markup=last.json.reply_markup
        keyboard = telebot.types.InlineKeyboardMarkup()
        item = last.json["reply_markup"]["inline_keyboard"][0]
        keyboard.row(
            telebot.types.InlineKeyboardButton(
                f'{item[0]["text"]}', callback_data=f'{item[0]["callback_data"]}'
            ),
            telebot.types.InlineKeyboardButton(
                f'{item[1]["text"]}', callback_data=f'{item[1]["callback_data"]}'
            ),
            telebot.types.InlineKeyboardButton(
                f'{item[2]["text"]}', callback_data=f'{item[2]["callback_data"]}'
            ),
        )
        keyboard.row(
            telebot.types.InlineKeyboardButton(
                "➕ show more",
                callback_data=f"games_show_more{last.json['reply_markup']['inline_keyboard'][1][0]['callback_data']}",
            )
        )
        keyboard.row(
            telebot.types.InlineKeyboardButton(
                f"🧾{get_betslip()}", callback_data="show_betslip"
            )
        )

        bot.edit_message_reply_markup(
            query.message.chat.id, last.id, reply_markup=keyboard
        )

    if data.startswith("show_betslip"):
        details = get_betslip()
        keyboard = telebot.types.InlineKeyboardMarkup()
        keyboard2 = telebot.types.InlineKeyboardMarkup()
        to_win = (amount * float(details.split(":")[1]))
        # update markup by removing show betslip
        item = query.json["message"]["reply_markup"]["inline_keyboard"][:-2][0]
        keyboard2.row(
            telebot.types.InlineKeyboardButton(
                f'{item[0]["text"]}', callback_data=f'{item[0]["callback_data"]}'
            ),
            telebot.types.InlineKeyboardButton(
                f'{item[1]["text"]}', callback_data=f'{item[1]["callback_data"]}'
            ),
            telebot.types.InlineKeyboardButton(
                f'{item[2]["text"]}', callback_data=f'{item[2]["callback_data"]}'
            ),
        )
        bot.edit_message_reply_markup(
            query.message.chat.id, query.message.id, reply_markup=keyboard2
        )
        for match in betslip:
            keyboard.row(
                telebot.types.InlineKeyboardButton(
                    f"❌ {Match.objects.get(match_id=match['game_id'])} - {match['selection']} - {match['odd']}",
                    callback_data=f'remove-odd/{match["game_id"]}/{match["selection"]}/{match["odd"]}',
                )
            )

        keyboard.row(
            telebot.types.InlineKeyboardButton(
                "-20", callback_data=f"wager_{amount-20}"
            ),
            telebot.types.InlineKeyboardButton(
                "-10", callback_data=f"wager_{amount-10}"
            ),
            telebot.types.InlineKeyboardButton(
                f"Amount: {amount}", callback_data="deposit"
            ),
            telebot.types.InlineKeyboardButton(
                "+10", callback_data=f"wager_{amount+10}"
            ),
            telebot.types.InlineKeyboardButton(
                "+20", callback_data=f"wager_{amount+20}"
            ),
        )
        keyboard.row(
            telebot.types.InlineKeyboardButton(
                f"✅  place bet to win {float('{:.2f}'.format(to_win))}",
                callback_data="place_bet",
            )
        )
        bot.send_message(
            query.message.chat.id,
            f"🧾 {details}",
            reply_markup=keyboard,
        )

    if data.startswith("remove"):
        details = get_betslip()
        to_win = (amount * float(details.split(":")[1]))

        def search_dict(dict_list, key, value):
            # searches betslip dict  and returns index if selection  already exsts
            for i, item in enumerate(dict_list):
                if item[key] == value:
                    return i
            return -1

        cd = data.split("/")
        match = {
            "game_id": f"{cd[1]}",
            "selection": f"{cd[2]}",
            "odd": f"{cd[3]}",
        }  # selected event and odds
        index = search_dict(betslip, "game_id", f"{cd[1]}")
        if index >= 0:
            if betslip[index]["selection"] == cd[2]:
                del betslip[index]
                bot.answer_callback_query(query.id, "removed from betslip")
            else:
                betslip[index]["selection"] = cd[2]
            bot.answer_callback_query(query.id, "betslip updated")
        bot.answer_callback_query(query.id, "betslip expired")
        keyboard = telebot.types.InlineKeyboardMarkup()
        for match in betslip:
            keyboard.row(
                telebot.types.InlineKeyboardButton(
                    f"❌ {Match.objects.get(match_id=match['game_id'])} - {match['selection']} - {match['odd']}",
                    callback_data=f'remove-odd/{match["game_id"]}/{match["selection"]}/{match["odd"]}',
                )
            )

        keyboard.row(
            telebot.types.InlineKeyboardButton(
                "-20", callback_data=f"wager_{amount-20}"
            ),
            telebot.types.InlineKeyboardButton(
                "-10", callback_data=f"wager_{amount-10}"
            ),
            telebot.types.InlineKeyboardButton(
                f"Amount: {amount}", callback_data="deposit"
            ),
            telebot.types.InlineKeyboardButton(
                "+10", callback_data=f"wager_{amount+10}"
            ),
            telebot.types.InlineKeyboardButton(
                "+20", callback_data=f"wager_{amount+20}"
            ),
        )
        keyboard.row(
            telebot.types.InlineKeyboardButton(
                f"✅  place bet to win {float('{:.2f}'.format(to_win))}",
                callback_data="place_bet",
            )
        )

        bot.edit_message_reply_markup(
            query.message.chat.id, query.message.id, reply_markup=keyboard
        )

    if data.startswith("wager"):
        details = get_betslip()
        amount = float(data.split("_")[1])
        keyboard = telebot.types.InlineKeyboardMarkup()

        for match in betslip:
            keyboard.row(
                telebot.types.InlineKeyboardButton(
                    f"❌ {Match.objects.get(match_id=match['game_id'])} - {match['selection']} - {match['odd']}",
                    callback_data=f'remove-odd/{match["game_id"]}/{match["selection"]}/{match["odd"]}',
                )
            )

        keyboard.row(
            telebot.types.InlineKeyboardButton(
                "-20", callback_data=f"wager_{amount-20}"
            ),
            telebot.types.InlineKeyboardButton(
                "-10", callback_data=f"wager_{amount-10}"
            ),
            telebot.types.InlineKeyboardButton(
                f"Amount: {amount}", callback_data="deposit"
            ),
            telebot.types.InlineKeyboardButton(
                "+10", callback_data=f"wager_{amount+10}"
            ),
            telebot.types.InlineKeyboardButton(
                "+20", callback_data=f"wager_{amount+20}"
            ),
        )
        keyboard.row(
            telebot.types.InlineKeyboardButton(
                f"✅  place bet to win{amount*float(details.split(':')[1])}",
                callback_data="place_bet",
            )
        )
        bot.edit_message_reply_markup(
            query.message.chat.id,
            query.message.id,
            reply_markup=keyboard,
        )

    if data.startswith("place"):
        keyboard = telebot.types.InlineKeyboardMarkup()
        currency=get_territory_currencies(user.profile.country.code)[0]
        if user.profile.balance > Money(amount,currency):
            betx = BetTicket.objects.create(
                user=user, stake_amount=amount, total_odds=1, prize=100
            )
            total_odds = 1

            for bet in betslip:
                match = Match.objects.get(match_id=bet["game_id"])
                selection = bet["selection"]
                if selection == "1":
                    odds = match.home_odds
                elif selection == "x":
                    odds = match.draw_odds
                elif selection == "2":
                    odds = match.away_odds

                total_odds *= odds

                pick = BetTicketSelection.objects.create(
                    bet_ticket=betx, match=match, selection=selection, odds=odds
                )
            betx.total_odds = total_odds
            betx.prize = amount * total_odds
            betx.save()
            user.profile.debit(amount)
            bot.answer_callback_query(query.id, "bet placed successfully, good luck!")
            keyboard.row(
                telebot.types.InlineKeyboardButton(
                    "back to home", callback_data="home"
                ),
            )
            bot.edit_message_reply_markup(
                query.message.chat.id,
                query.message.id,
                reply_markup=keyboard,
            )
        else:
            bot.answer_callback_query(query.id, "insufficient balance")
            keyboard.row(
                telebot.types.InlineKeyboardButton(
                    "deposit", callback_data="deposit"
                ),
            )
            bot.edit_message_reply_markup(
                query.message.chat.id,
                query.message.id,
                reply_markup=keyboard,
            )

    if data.startswith("home"):
        home(query.message, user)

    if data.startswith("deposit"):
        markup = types.ForceReply(selective=False)
        bot.send_message(query.message.chat.id, "Enter deposit amount:", reply_markup=markup)
        

    if data.startswith("account"):
        keyboard = telebot.types.InlineKeyboardMarkup()
        keyboard.row(
        telebot.types.InlineKeyboardButton("⬆️ Deposit", callback_data="deposit")
    )
        keyboard.row(
        telebot.types.InlineKeyboardButton("⬇️ Withdraw", callback_data="withdraw")
    )
        keyboard.row(
        telebot.types.InlineKeyboardButton("🎟️ My bets", callback_data="mybets")
    )
        keyboard.row(
        telebot.types.InlineKeyboardButton("👥 Referrals", callback_data="referrals")
    )
        keyboard.row(
        telebot.types.InlineKeyboardButton("⚙️ Settings", callback_data="settings")
    )
        bot.send_message(query.message.chat.id, "My Account:", reply_markup=keyboard)


    if data.startswith("withdraw"):
        keyboard = telebot.types.InlineKeyboardMarkup()
        markup = types.ForceReply(selective=False)
        bot.send_message(query.message.chat.id, f"Enter withdraw amount: max {user.profile.balance}", reply_markup=markup)
    

    if data.startswith("referrals"):
        keyboard = telebot.types.InlineKeyboardMarkup()
        ref=Profile.objects.filter(referee=user)
        val=ref.filter(is_valid=True)
        keyboard.row(
        telebot.types.InlineKeyboardButton("redeem", callback_data='redeem'))
        bot.send_message(query.message.chat.id, f"Share link: https://t.me/surebet_bot?start={user.profile.referral_id} \n Total referrals: {ref.count()} \n Valid referrals: {val.count()} \n Redeemed: {user.profile.redeem} \n Available for redemption: {val.count()-user.profile.redeem}",reply_markup=keyboard)


    if data.startswith("redeem"):
        markup = types.ForceReply(selective=False)
        ref=Profile.objects.filter(referee=user)
        val=ref.filter(is_valid=True)
        num=val.count()-user.profile.redeem
        currency=get_territory_currencies(user.profile.country.code)[0]
        cred=convert_money(Money(50*num, "KES"),currency)

        bot.send_message(query.message.chat.id, f'Available for redemption: {num} ≈ {cred}')
        bot.send_message(query.message.chat.id, f'Enter number to redeem: \n Minimum: 5', reply_markup=markup)



    if data.startswith("settings"):
        keyboard = telebot.types.InlineKeyboardMarkup()
        keyboard.row(
    telebot.types.InlineKeyboardButton(f"country: {user.profile.country.unicode_flag}", callback_data='country')
)
        bot.send_message(query.message.chat.id,'settings', reply_markup=keyboard)
        
    if data.startswith("country"):
        markup = types.ForceReply(selective=False)
        bot.send_message(query.message.chat.id,'Enter country short code eg. USA:', reply_markup=markup)

    if data.startswith("unicode"):
        country=data.split('-')[1]
        user.profile.country=country
        currency=get_territory_currencies(user.profile.country.code)[0]
        user.profile.balance=convert_money(user.profile.balance, currency)
        user.profile.total_deposit=convert_money(user.profile.total_deposit, currency)
        user.save()
        bot.answer_callback_query(query.id, "successfully changed")
        home(query.message, user)
    
    if data.startswith("mybets"):
        keyboard = telebot.types.InlineKeyboardMarkup()
        tickets=BetTicket.objects.filter(user=user)
        if tickets:
            if tickets.filter(is_settled=False) == None:
                keyboard.row(
                telebot.types.InlineKeyboardButton("No active bets, Show expired:", callback_data='all_tickets'))
                keyboard.row(
                telebot.types.InlineKeyboardButton("Back to home:", callback_data='home'))


            else:
                for ticket in tickets.filter(is_settled=False):
                    keyboard.row(
                    telebot.types.InlineKeyboardButton(str(ticket), callback_data=f'ticket-{ticket.id}'))
                keyboard.row(
                    telebot.types.InlineKeyboardButton("Show expired:", callback_data='all_tickets'))
                keyboard.row(
                    telebot.types.InlineKeyboardButton("Back to home:", callback_data='home'))


        else:
            keyboard.row(
                    telebot.types.InlineKeyboardButton("No previous bets, Back to home", callback_data='home'))


        bot.send_message(query.message.chat.id,'Active bets       ', reply_markup=keyboard)

    if data.startswith("all_tickets"):
        pass

    if data.startswith("ticket"):
        keyboard = telebot.types.InlineKeyboardMarkup()
        keyboard.row(
            telebot.types.InlineKeyboardButton("Back to bets", callback_data="mybets"))
        ticket_id=data.split('-')[1]
        ticket=BetTicket.objects.get(id=ticket_id)
        msg=''
        for selection in ticket.sselections.all():
            msg+=f'{selection.match.home} vs {selection.match.away} - ({selection.selection}) {"🕘" if selection.match.stage!="fin" else ("✅" if selection.is_correct() else "❌")}\n'
        bot.send_message(query.message.chat.id,msg, reply_markup=keyboard)


bot.infinity_polling()