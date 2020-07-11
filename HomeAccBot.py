import argparse
import datetime
import json
import requests
from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext, MessageHandler, Filters

RANDOM_DOGO_API = 'https://random.dog/woof.json'
HOME_ACC_POST_EXPENSE_API = 'http://localhost/Home/hs/HomeAcc/exp/postexpense'
HOME_ACC_POST_INCOME_API = 'http://localhost/Home/hs/HomeAcc/exp/postincome'
HOME_ACC_POST_TRANSFER_API = 'http://localhost/Home/hs/HomeAcc/trn/posttransfer'


def default(o):
    if isinstance(o, (datetime.date, datetime.datetime)):
        return o.isoformat()


def get_url():
    contents = requests.get(RANDOM_DOGO_API).json()
    url = contents['url']
    return url


def dogo(update: Update, context: CallbackContext):
    url = get_url()
    chat_id = update.message.chat_id
    context.bot.send_photo(chat_id=chat_id, photo=url)
    context.bot.send_message(chat_id=update.message.chat_id,
                             text=f'/help')


def help(update: Update, context: CallbackContext):
    context.bot.send_message(chat_id=update.message.chat_id,
                             text=f'Регистрация расхода: расход питание карта1 150\n'
                                  'Регистрация перемещения средств: перемещение карта1 карта2 150\n'
                                  'Регистрация дохода: доход зп карта1 150000\n'
                                  'Собакен: /dogo /help'
                             )


def expense(update: Update, context: CallbackContext):
    # print(context.match.groups())
    data_to_post = {
        'id': f'{update.message.chat.id}-{update.message.message_id}',
        'expense': context.match.groups()[0],
        'wallet': context.match.groups()[1],
        'sum': context.match.groups()[2],
        'date': update.message.date
    }
    response = requests.post(HOME_ACC_POST_EXPENSE_API,
                             data=json.dumps(data_to_post, sort_keys=True, indent=1, default=default),
                             headers={"Content-Type": "application/json"})

    context.bot.send_message(chat_id=update.message.chat_id,
                             text=f'{response.text} ({response.status_code}) /help',
                             reply_to_message_id=update.message.message_id)


def income(update: Update, context: CallbackContext):
    # print(context.match.groups())
    data_to_post = {
        'id': f'{update.message.chat.id}-{update.message.message_id}',
        'income': context.match.groups()[0],
        'wallet': context.match.groups()[1],
        'sum': context.match.groups()[2],
        'date': update.message.date
    }
    response = requests.post(HOME_ACC_POST_INCOME_API,
                             data=json.dumps(data_to_post, sort_keys=True, indent=1, default=default),
                             headers={"Content-Type": "application/json"})

    context.bot.send_message(chat_id=update.message.chat_id,
                             text=f'{response.text} ({response.status_code}) /help',
                             reply_to_message_id=update.message.message_id)


def transfer(update: Update, context: CallbackContext):
    # print(context.match.groups())
    data_to_post = {
        'id': f'{update.message.chat.id}-{update.message.message_id}',
        'wallet1': context.match.groups()[0],
        'wallet2': context.match.groups()[1],
        'sum': context.match.groups()[2],
        'date': update.message.date
    }
    response = requests.post(HOME_ACC_POST_TRANSFER_API,
                             data=json.dumps(data_to_post, sort_keys=True, indent=1, default=default),
                             headers={"Content-Type": "application/json"})

    context.bot.send_message(chat_id=update.message.chat_id,
                             text=f'{response.text} ({response.status_code}) /help',
                             reply_to_message_id=update.message.message_id)


def main(args):

    if args.proxy_url:
        REQUEST_KWARGS = {
            'proxy_url': args.proxy_url,
            # Optional, if you need authentication:
            'urllib3_proxy_kwargs': {
                'username': args.proxy_user,
                'password': args.proxy_password
            }
        }
    else:
        REQUEST_KWARGS = {}

    updater = Updater(args.token, request_kwargs=REQUEST_KWARGS, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler('dogo', dogo))
    dp.add_handler(CommandHandler('help', help))
    dp.add_handler(MessageHandler(Filters.regex('[Рр]{1}асход ([а-яА-Я]+) ([а-яА-Я0-9]+) ([\d]+)'), expense))
    dp.add_handler(MessageHandler(Filters.regex('[Пп]{1}еремещение ([а-яА-Я0-9]+) ([а-яА-Я0-9]+) ([\d]+)'), transfer))
    dp.add_handler(MessageHandler(Filters.regex('[Дд]{1}одод ([а-яА-Я0-9]+) ([а-яА-Я0-9]+) ([\d]+)'), income))
    updater.start_polling()
    updater.idle()


parser = argparse.ArgumentParser(description='Process telegram token.')

parser.add_argument('-t', '--token', type=str, help='telegram token', required=True)
parser.add_argument('-u', '--proxy_url', type=str, help='proxy URL')
parser.add_argument('-s', '--proxy_user', type=str, help='proxy user')
parser.add_argument('-p', '--proxy_password', type=str, help='proxy password')

if __name__ == '__main__':
    main(parser.parse_args())
