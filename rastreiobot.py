from bs4 import BeautifulSoup
from check_update import check_update
from time import time
from pymongo import MongoClient
from telebot import types
import configparser
import requests
import sys
import telebot

config = configparser.ConfigParser()
config.sections()
config.read('bot.conf')

TOKEN = config['RASTREIOBOT']['TOKEN']
int_check = int(config['RASTREIOBOT']['int_check'])
bot = telebot.TeleBot(TOKEN)

client = MongoClient()
db = client.rastreiobot

user_dict = []
class User:
    def __init__(self, chatid):
        self.chatid = chatid
        self.code = None
        self.desc = None

def check_package(code):
    cursor = db.rastreiobot.find_one({"code": code.upper()})
    if cursor:
        return True
    return False

def list_packages(chatid, done):
    cursor = db.rastreiobot.find()
    aux = ''
    for elem in cursor:
        if str(chatid) in elem['users']:
            # print(elem['code'])
            # print(elem['stat'][len(elem['stat'])-1])
            if not done:
                if 'Entrega Efetuada' not in elem['stat'][len(elem['stat'])-1]:
                    aux = aux + '/' + elem['code']
                    try:
                        if elem[str(chatid)] != elem['code']:
                            aux = aux + ' ' +  elem[str(chatid)]
                    except:
                        pass
                    aux = aux + '\n'
            else:
                if 'Entrega Efetuada' in elem['stat'][len(elem['stat'])-1]:
                    aux = aux + elem['code']
                    try:
                        if elem[str(chatid)] != elem['code']:
                            aux = aux + ' ' +  elem[str(chatid)]
                    except:
                        pass
                    aux = aux + '\n'
    return aux

def status_package(code):
    cursor = db.rastreiobot.find_one(
    {
        "code": code
    })
    return cursor['stat']

def check_user(code, user):
    cursor = db.rastreiobot.find_one(
    {
            "code": code.upper(),
            "users": user
    })
    if cursor:
        return True
    return False

def add_package(code, user):
    # import ipdb; ipdb.set_trace()
    stat = get_update(code)
    if stat == 0:
        return stat
    elif stat == 1:
        return stat
    else:
        cursor = db.rastreiobot.insert_one (
        {
            "code" : code.upper(),
            "users" : [user],
            "stat" : stat,
            "time" : str(time())
        })
        stat = 10
    return stat

def add_user(code, user):
    cursor = db.rastreiobot.update_one (
    { "code" : code.upper() },
    {
        "$push": {
            "users" : user
        }
    })

def set_desc(code, user, desc):
    # print('Descrição: ' + str(desc))
    if not desc:
        desc = code
    cursor = db.rastreiobot.update_one (
    { "code" : code.upper() },
    {
        "$set": {
            user : desc
        }
    })

def get_update(code):
    return check_update(code)

@bot.message_handler(commands=['start', 'Repetir', 'Historico'])
def echo_all(message):
    markup = types.ReplyKeyboardRemove(selective=False)
    chatid = message.from_user.id
    mensagem = message.text
    bot.send_message(chatid,
        str(u'\U0001F4EE') + '<b>@RastreioBot!</b>\n\n'
        'Por favor, envie um código de objeto.\n\n' +
        'Para adicionar uma descrição, envie um código ' +
        'seguido da descrição.\n\n' +
        '<i>PN123456789BR Minha encomenda</i>'
        , parse_mode='HTML', reply_markup=markup
    )

@bot.message_handler(commands=['pacotes'])
def echo_all(message):
    chatid = message.from_user.id
    message = list_packages(chatid, False)
    if len(message) < 1:
        message = "Nenhum pacote encontrado."
    else:
        message = 'Clique para ver o histórico de cada um.\n' + message
    bot.send_message(chatid, message)

@bot.message_handler(commands=['concluidos'])
def echo_all(message):
    chatid = message.from_user.id
    message = list_packages(chatid, True)
    if len(message) < 1:
        message = "Nenhum pacote encontrado."
    else:
        message = 'Pacotes concluídos.\n' + message
    bot.send_message(chatid, message)

@bot.message_handler(commands=['info', 'Info'])
def echo_all(message):
    chatid = message.from_user.id
    bot.send_message(chatid, 'Bot por @GabrielRF.\n\nAvalie o bot:' 
        + '\nhttps://telegram.me/storebot?start=rastreiobot', 
        disable_web_page_preview=True)

@bot.message_handler(func=lambda m: True)
def echo_all(message):
    user = str(message.from_user.id)
    code = str(message.text.split(' ')[0]).replace('/','')
    code = code.upper()
    try:
        desc = str(message.text.split(' ', 1)[1])
    except:
        desc = code
    # print(code)
    # print(message.from_user.id)
    bot.send_chat_action(message.from_user.id, 'typing')
    if len(code) == 13:
        cursor = db.rastreiobot.find()
        exists = check_package(code)
        if exists:
            exists = check_user(code, user)
            if not exists:
                add_user(code, user)
            status = status_package(code)
            message = ''
            for status in status_package(code):
                message = message + '\n\n' + status
            bot.send_message(user, message, parse_mode='HTML')
            if desc != code:
                set_desc(str(code), str(user), desc)
        else:
            stat = add_package(str(code), str(user))
            if stat == 0:
                bot.reply_to(message, 'Correios fora do ar')
            elif stat == 1:
                bot.reply_to(message,
                    'Código não foi encontrado no sistema dos Correios.\n'
                    + 'Talvez seja necessário aguardar algumas horas para'
                    + ' que esteja disponível para consultas.'
                )
            elif stat == 10:
                set_desc(str(code), str(user), desc)
                msg = bot.reply_to(message, 'Pacote cadastrado.')
                status = status_package(code)
                last = len(status)-1
                bot.send_message(user,
                    status_package(code)[last], parse_mode='HTML'
                )
    else:
        bot.reply_to(message, "Erro.\nVerifique se o código foi digitado corretamente.")

bot.polling()
