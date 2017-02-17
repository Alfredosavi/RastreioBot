from bs4 import BeautifulSoup
from check_update import check_update
from datetime import datetime
from time import time
from pymongo import MongoClient
from telebot import types

import configparser
import logging
import logging.handlers
import requests
import sys
import telebot

config = configparser.ConfigParser()
config.sections()
config.read('bot.conf')

TOKEN = config['RASTREIOBOT']['TOKEN']
int_check = int(config['RASTREIOBOT']['int_check'])
LOG_INFO_FILE = config['RASTREIOBOT']['log_file']

logger_info = logging.getLogger('InfoLogger')
logger_info.setLevel(logging.DEBUG)
handler_info = logging.handlers.RotatingFileHandler(LOG_INFO_FILE,
    maxBytes=10240, backupCount=5, encoding='utf-8')
logger_info.addHandler(handler_info)

bot = telebot.TeleBot(TOKEN)
client = MongoClient()
db = client.rastreiobot

## Check if package exists in DB
def check_package(code):
    cursor = db.rastreiobot.find_one({"code": code.upper()})
    if cursor:
        return True
    return False

## List packages of a user
def list_packages(chatid, done):
    cursor = db.rastreiobot.find()
    aux = ''
    for elem in cursor:
        if str(chatid) in elem['users']:
            # print(elem['code'] + str(elem['users']))
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

## Get last state of a package from DB 
def status_package(code):
    cursor = db.rastreiobot.find_one(
    {
        "code": code
    })
    return cursor['stat']

## Check if user exists on a specific tracking code
def check_user(code, user):
    cursor = db.rastreiobot.find_one(
    {
            "code": code.upper(),
            "users": user
    })
    if cursor:
        return True
    return False

## Insert package on DB
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

## Add a user to a package that exists on DB
def add_user(code, user):
    cursor = db.rastreiobot.update_one (
    { "code" : code.upper() },
    {
        "$push": {
            "users" : user
        }
    })

def del_user(code, user):
    cursor = db.rastreiobot.update (
    { "code" : code.upper() },
    {
        "$pull": {
            "users" : str(user)
        }
    })
    print(str(cursor))

## Set a description to a package
def set_desc(code, user, desc):
    if not desc:
        desc = code
    cursor = db.rastreiobot.update_one (
    { "code" : code.upper() },
    {
        "$set": {
            user : desc
        }
    })

## Update package tracking state
def get_update(code):
    return check_update(code)

## Add to log
def log_text(chatid, message_id, text):
    logger_info.info(
        str(datetime.now())
        + '\t' + str(chatid)
        + '\t' + str(message_id)
        + ' \t' + str(text)
    )

@bot.message_handler(commands=['start', 'Repetir', 'Historico'])
def echo_all(message):
    bot.send_chat_action(message.chat.id, 'typing')
    log_text(message.chat.id, message.message_id, message.text)
    markup = types.ReplyKeyboardRemove(selective=False)
    chatid = message.chat.id
    mensagem = message.text
    user = (str(u'\U0001F4EE') + '<b>@RastreioBot!</b>\n\n'
        'Por favor, envie um código de objeto.\n\n' +
        'Para adicionar uma descrição, envie um código ' +
        'seguido da descrição.\n\n' +
        '<i>PN123456789BR Minha encomenda</i>')
    group = (str(u'\U0001F4EE') + '<b>@RastreioBot!</b>\n\n'
        'Por favor, envie um código de objeto.\n\n' +
        'Para adicionar uma descrição, envie um código ' +
        'seguido da descrição.\n\n' +
        '<i>/PN123456789BR Minha encomenda</i>')
    if message.chat.id > 0:
        bot.send_message(message.chat.id, user, parse_mode='HTML')
    else:
        bot.send_message(message.chat.id, group, parse_mode='HTML')

@bot.message_handler(commands=['pacotes'])
def echo_all(message):
    bot.send_chat_action(message.chat.id, 'typing')
    log_text(message.chat.id, message.message_id, message.text)
    chatid = message.chat.id
    message = list_packages(chatid, False)
    if len(message) < 1:
        message = "Nenhum pacote encontrado."
    else:
        message = '<b>Clique para ver o histórico:</b>\n' + message
    bot.send_message(chatid, message, parse_mode='HTML')

@bot.message_handler(commands=['concluidos'])
def echo_all(message):
    bot.send_chat_action(message.chat.id, 'typing')
    log_text(message.chat.id, message.message_id, message.text)
    chatid = message.chat.id
    message = list_packages(chatid, True)
    if len(message) < 1:
        message = "Nenhum pacote encontrado."
    else:
        message = '<b>Pacotes concluídos nos últimos 30 dias:</b>\n' + message
    bot.send_message(chatid, message, parse_mode='HTML')

@bot.message_handler(commands=['info', 'Info'])
def echo_all(message):
    bot.send_chat_action(message.chat.id, 'typing')
    log_text(message.chat.id, message.message_id, message.text)
    chatid = message.chat.id
    bot.send_message(chatid, 'Bot por @GabrielRF.\n\nAvalie o bot:' 
        + '\nhttps://telegram.me/storebot?start=rastreiobot\n\n'
        + 'Bot open source:\nhttps://github.com/GabrielRF/RastreioBot'
        + '\n\nConheça meus outros projetos:'
        + '\nhttp://grf.xyz/telegrambr'
        + '\n\nColabore!'
        + '\nhttp://grf.xyz/paypal', 
        disable_web_page_preview=True)

@bot.message_handler(content_types=['document', 'audio', 'photo'])
def echo_all(message):
    bot.reply_to(message, 'Formato inválido')
    log_text(message.chat.id, message.message_id, 'Formato inválido')

@bot.message_handler(func=lambda m: True)
def echo_all(message):
    bot.send_chat_action(message.chat.id, 'typing')
    log_text(message.chat.id, message.message_id, message.text)
    user = str(message.chat.id)
    code = str(message.text.split(' ')[0]).replace('/','')
    code = code.upper()
    code = code.replace('@RASTREIOBOT', '')
    try:
        desc = str(message.text.split(' ', 1)[1])
    except:
        desc = code
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
        if int(user) > 0:
            bot.reply_to(message, "Erro.\nVerifique se o código foi digitado corretamente.")

bot.polling()
