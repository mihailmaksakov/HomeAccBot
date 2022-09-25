import argparse
import datetime
import json
import requests
from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext, MessageHandler, Filters, CallbackQueryHandler, \
    ConversationHandler
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton, \
    ReplyKeyboardRemove

HOME_ACC_SERVER = 'http://localhost:81'

RANDOM_DOGO_API = 'https://random.dog/woof.json'
HOME_ACC_POST_EXPENSE_API = f'{HOME_ACC_SERVER}/home_acc/hs/HomeAcc/exp/postexpense'
HOME_ACC_POST_INCOME_API = f'{HOME_ACC_SERVER}/home_acc/hs/HomeAcc/inc/postincome'
HOME_ACC_POST_TRANSFER_API = f'{HOME_ACC_SERVER}/home_acc/hs/HomeAcc/trn/posttransfer'
HOME_ACC_GET_BALANCE_API = f'{HOME_ACC_SERVER}/home_acc/hs/HomeAcc/balance/get'
HOME_ACC_GET_EXPENSES_API = f'{HOME_ACC_SERVER}/home_acc/hs/HomeAcc/expenses/get'
HOME_ACC_GET_INCOMES_API = f'{HOME_ACC_SERVER}/home_acc/hs/HomeAcc/incomes/get'
HOME_ACC_GET_WALLETS_API = f'{HOME_ACC_SERVER}/home_acc/hs/HomeAcc/wallets/get'

EXPENSE, FIX_EXPENSE, EXPENSE_SUM = range(3)
INCOME, FIX_INCOME, INCOME_SUM = range(3)
SHOW_BALANCE = range(1)
TR_WALLET2, FIX_WALLET2, TRANSFER_SUM = range(3)

EXPENSE_POST = {}
INCOME_POST = {}
TRANSFER_POST = {}


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
                             # 'Остаток /balance \n'
                                  'Собакен: /dogo \n'
                                  '/help'
                             )


def post_expense_manual(update: Update, context: CallbackContext):
    post_local = {
        'id': f'{update.message.chat.id}-{update.message.message_id}',
        'expense': context.match.groups()[0],
        'wallet': context.match.groups()[1],
        'sum': context.match.groups()[2],
        'date': update.message.date,
        'by_id': "0"
    }

    response = requests.post(HOME_ACC_POST_EXPENSE_API,
                             data=json.dumps(post_local, sort_keys=True, indent=1, default=default),
                             headers={"Content-Type": "application/json"})

    context.bot.send_message(chat_id=update.message.chat_id,
                             text=f'{response.text} ({response.status_code})\n /help',
                             reply_to_message_id=update.message.message_id)


def post_expense(update: Update, context: CallbackContext):
    global EXPENSE_POST

    EXPENSE_POST['id'] = f'{update.message.chat.id}-{update.message.message_id}'
    EXPENSE_POST['date'] = update.message.date
    EXPENSE_POST['by_id'] = "1"

    response = requests.post(HOME_ACC_POST_EXPENSE_API,
                             data=json.dumps(EXPENSE_POST, sort_keys=True, indent=1, default=default),
                             headers={"Content-Type": "application/json"})

    context.bot.send_message(chat_id=update.message.chat_id,
                             text=f'{response.text} ({response.status_code})',
                             reply_to_message_id=update.message.message_id)

    EXPENSE_POST = {}


def post_income(update: Update, context: CallbackContext):
    global INCOME_POST

    INCOME_POST['id'] = f'{update.message.chat.id}-{update.message.message_id}'
    INCOME_POST['date'] = update.message.date
    INCOME_POST['by_id'] = "1"

    response = requests.post(HOME_ACC_POST_INCOME_API,
                             data=json.dumps(INCOME_POST, sort_keys=True, indent=1, default=default),
                             headers={"Content-Type": "application/json"})

    context.bot.send_message(chat_id=update.message.chat_id,
                             text=f'{response.text} ({response.status_code})',
                             reply_to_message_id=update.message.message_id)

    INCOME_POST = {}


def post_transfer(update: Update, context: CallbackContext):
    global TRANSFER_POST

    TRANSFER_POST['id'] = f'{update.message.chat.id}-{update.message.message_id}'
    TRANSFER_POST['date'] = update.message.date
    TRANSFER_POST['by_id'] = "1"

    # data_to_post = {
    #     'id': f'{update.message.chat.id}-{update.message.message_id}',
    #     'wallet1': context.match.groups()[0],
    #     'wallet2': context.match.groups()[1],
    #     'sum': context.match.groups()[2],
    #     'date': update.message.date
    # }
    response = requests.post(HOME_ACC_POST_TRANSFER_API,
                             data=json.dumps(TRANSFER_POST, sort_keys=True, indent=1, default=default),
                             headers={"Content-Type": "application/json"})

    context.bot.send_message(chat_id=update.message.chat_id,
                             text=f'{response.text} ({response.status_code})',
                             reply_to_message_id=update.message.message_id)


def balance(update: Update, context: CallbackContext):
    choose_wallet_with_total(update, update.message)

    return SHOW_BALANCE


def show_balance(update: Update, context):
    wallet = update.callback_query.data.split('_')[1]

    response = requests.get(HOME_ACC_GET_BALANCE_API,
                            data='',
                            headers={"Content-Type": "application/json"})

    balance_a = json.loads(response.text)

    res = [(i['value'], i['currency']) for i in balance_a if i['wallet'] == wallet]
    value, currency = res.pop() if res else (0, '')

    update.callback_query.message.edit_text(f'{wallet_name_by_id(get_wallets(True), wallet)}: {value} ({currency})',
                                            reply_markup=None)

    return ConversationHandler.END


def get_wallets(with_totals=False):
    response = requests.get(HOME_ACC_GET_WALLETS_API,
                            data='',
                            headers={"Content-Type": "application/json"})

    res = json.loads(response.text)
    if with_totals:
        res.append({'id': 'total', 'name': 'ИТОГО'})

    return res


def get_expenses():
    response = requests.get(HOME_ACC_GET_EXPENSES_API,
                            data='',
                            headers={"Content-Type": "application/json"})
    return json.loads(response.text)


def get_incomes():
    response = requests.get(HOME_ACC_GET_INCOMES_API,
                            data='',
                            headers={"Content-Type": "application/json"})
    return json.loads(response.text)


def wallet_name_by_id(wallets, wallet_id):
    result = [w['name'] for w in wallets if w['id'] == wallet_id]
    return result[0] if result else 'undefined'


def choose_wallet_with_total(update, message):
    wallets = get_wallets(True)
    choose_wallet(update, message, wallets)


def choose_wallet(update, message, wallets, postfix=''):
    keyboard = [[InlineKeyboardButton(i["name"],
                                      callback_data=f'w_{i["id"]}')] for i in wallets]
    reply_markup = InlineKeyboardMarkup(keyboard)
    message.reply_text(f'Выберите кошелек {postfix if postfix else ""}:', reply_markup=reply_markup)


# def start(update: Update, context: CallbackContext):
#     keyboard = [[KeyboardButton(text='/help - Помощь')]]
#     # keyboard = [['/help', 'EN']]
#
#     reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
#     update.message.reply_text('Выберите кошелек:', reply_markup=reply_markup)


def end(update, _):
    update.message.reply_text('Операция отменена', reply_markup=None)
    return ConversationHandler.END


def expense(update, context):
    global EXPENSE_POST

    EXPENSE_POST = {}

    choose_wallet(update, update.message, get_wallets())

    return EXPENSE


def choose_expense(update, context):
    global EXPENSE_POST

    EXPENSE_POST['wallet'] = update.callback_query.data.split('_')[1]

    expenses = get_expenses()

    keyboard = [[InlineKeyboardButton(expenses[i]['name'], callback_data=f'e_{expenses[i]["id"]}'),
                 InlineKeyboardButton(expenses[i + 1]['name'], callback_data=f'e_{expenses[i + 1]["id"]}')] for i in
                range(0, len(expenses) - len(expenses) % 2, 2)]
    if len(expenses) % 2:
        keyboard.append([InlineKeyboardButton(expenses[-1]['name'], callback_data=f'e_{expenses[-1]["id"]}')])

    reply_markup = InlineKeyboardMarkup(keyboard)
    update.callback_query.message.reply_text('Выберите вид расхода', reply_markup=reply_markup)

    return FIX_EXPENSE


def fix_expense(update, context):
    global EXPENSE_POST

    EXPENSE_POST['expense'] = update.callback_query.data.split('_')[1]

    update.callback_query.message.reply_text('Введите сумму', reply_markup=None)

    return EXPENSE_SUM


def enter_expense_sum(update, context):
    global EXPENSE_POST

    EXPENSE_POST['sum'] = int(update.message.text)

    post_expense(update, context)

    return ConversationHandler.END


def income(update, context):
    global INCOME_POST

    INCOME_POST = {}

    choose_wallet(update, update.message, get_wallets())

    return INCOME


def choose_income(update, context):
    global INCOME_POST

    INCOME_POST['wallet'] = update.callback_query.data.split('_')[1]

    incomes = get_incomes()

    keyboard = [[InlineKeyboardButton(incomes[i]['name'], callback_data=f'e_{incomes[i]["id"]}'),
                 InlineKeyboardButton(incomes[i + 1]['name'], callback_data=f'e_{incomes[i + 1]["id"]}')] for i in
                range(0, len(incomes) - len(incomes) % 2, 2)]
    if len(incomes) % 2:
        keyboard.append([InlineKeyboardButton(incomes[-1]['name'], callback_data=f'e_{incomes[-1]["id"]}')])

    reply_markup = InlineKeyboardMarkup(keyboard)
    update.callback_query.message.reply_text('Выберите вид дохода', reply_markup=reply_markup)

    return FIX_INCOME


def fix_income(update, context):
    global INCOME_POST

    INCOME_POST['income'] = update.callback_query.data.split('_')[1]

    update.callback_query.message.reply_text('Введите сумму', reply_markup=None)

    return INCOME_SUM


def enter_income_sum(update, context):
    global INCOME_POST

    INCOME_POST['sum'] = int(update.message.text)

    post_income(update, context)

    return ConversationHandler.END


def transfer(update, context):
    global TRANSFER_POST

    TRANSFER_POST = {}

    choose_wallet(update, update.message, get_wallets(), '(списание)')

    return TR_WALLET2


def choose_wallet2(update, context):
    global TRANSFER_POST

    TRANSFER_POST['wallet1'] = update.callback_query.data.split('_')[1]

    choose_wallet(update, update.callback_query.message, get_wallets(), '(зачисление)')

    return FIX_WALLET2


def fix_wallet2(update, context):
    global TRANSFER_POST

    TRANSFER_POST['wallet2'] = update.callback_query.data.split('_')[1]

    update.callback_query.message.reply_text('Введите сумму', reply_markup=None)

    return TRANSFER_SUM


def enter_transfer_sum(update, context):
    global TRANSFER_POST

    TRANSFER_POST['sum'] = int(update.message.text)

    post_transfer(update, context)

    return ConversationHandler.END


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

    # dp.add_handler(CommandHandler('start', start))
    dp.add_handler(CommandHandler('dogo', dogo))
    dp.add_handler(CommandHandler('help', help))
    # dp.add_handler(CommandHandler('balance', balance))
    dp.add_handler(
        MessageHandler(Filters.regex('[Рр]{1}асход ([а-яА-Я]+) ([а-яА-Я0-9]+) ([\d]+)'), post_expense_manual))
    # dp.add_handler(MessageHandler(Filters.regex('[Пп]{1}еремещение ([а-яА-Я0-9]+) ([а-яА-Я0-9]+) ([\d]+)'), post_transfer_manual))
    # dp.add_handler(MessageHandler(Filters.regex('[Дд]{1}оход ([а-яА-Я0-9]+) ([а-яА-Я0-9]+) ([\d]+)'), post_income_manual))
    # dp.add_handler(MessageHandler(Filters.regex('[Оо]{1}статок'), balance))
    # dp.add_handler(CallbackQueryHandler(button))

    conv_handler_e = ConversationHandler(
        entry_points=[CommandHandler('expense', expense)],
        states={
            EXPENSE: [
                CallbackQueryHandler(choose_expense),
                CommandHandler('end', end)
            ],
            FIX_EXPENSE: [
                CallbackQueryHandler(fix_expense),
                CommandHandler('end', end)
            ],
            EXPENSE_SUM: [
                MessageHandler(Filters.regex('^([\d]+)$'), enter_expense_sum),
                CommandHandler('end', end)
            ],
        },
        fallbacks=[CommandHandler('end', end)],
    )

    dp.add_handler(conv_handler_e)

    conv_handler_i = ConversationHandler(
        entry_points=[CommandHandler('income', income)],
        states={
            INCOME: [
                CallbackQueryHandler(choose_income),
                CommandHandler('end', end)
            ],
            FIX_INCOME: [
                CallbackQueryHandler(fix_income),
                CommandHandler('end', end)
            ],
            INCOME_SUM: [
                MessageHandler(Filters.regex('^([\d]+)$'), enter_income_sum),
                CommandHandler('end', end)
            ],
        },
        fallbacks=[CommandHandler('end', end)],
    )

    dp.add_handler(conv_handler_i)

    conv_handler_b = ConversationHandler(
        entry_points=[CommandHandler('balance', balance)],
        states={
            SHOW_BALANCE: [
                CallbackQueryHandler(show_balance),
                CommandHandler('end', end)
            ],
        },
        fallbacks=[CommandHandler('end', end)],
    )

    dp.add_handler(conv_handler_b)

    conv_handler_t = ConversationHandler(
        entry_points=[CommandHandler('transfer', transfer)],
        states={
            TR_WALLET2: [
                CallbackQueryHandler(choose_wallet2),
                CommandHandler('end', end)
            ],
            FIX_WALLET2: [
                CallbackQueryHandler(fix_wallet2),
                CommandHandler('end', end)
            ],
            TRANSFER_SUM: [
                MessageHandler(Filters.regex('^([\d]+)$'), enter_transfer_sum),
                CommandHandler('end', end)
            ],
        },
        fallbacks=[CommandHandler('end', end)],
    )

    dp.add_handler(conv_handler_t)

    updater.start_polling()
    updater.idle()


parser = argparse.ArgumentParser(description='Process telegram token.')

parser.add_argument('-t', '--token', type=str, help='telegram token', required=True)
parser.add_argument('-u', '--proxy_url', type=str, help='proxy URL')
parser.add_argument('-s', '--proxy_user', type=str, help='proxy user')
parser.add_argument('-p', '--proxy_password', type=str, help='proxy password')

if __name__ == '__main__':
    main(parser.parse_args())
