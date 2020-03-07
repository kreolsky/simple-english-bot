import telebot
import redis
import os
import time
import pickle
import random

from .classes import MessageHandler
from .classes import Translator
from .classes import UserStorage
from .tools import def_to_str, dict_to_str

from settings import telebot_token
from settings import yandex_api_key

bot = telebot.TeleBot(telebot_token)
redis_server = redis.Redis(host='redis', db=0)
# redis_server = redis.Redis(host="127.0.0.1", port=6399, db=0)

parser = MessageHandler()
dict = Translator(yandex_api_key, redis_server)

def translate_and_send(text_to_translate, user_id):
    out = dict.translate(text_to_translate, ui='ru')['def']
    result = def_to_str(out) if out else f'"{text_to_translate}" not found'
    bot.send_message(user_id, result, parse_mode='markdown')

@parser.command(['/translate', '/t'])
def translate_word(message):
    user_id = str(message['message']['from']['id'])
    text_to_translate = ' '.join(message['message']['text'].split(' ')[1:])
    translate_and_send(text_to_translate, user_id)

@parser.command(['/add', '/a'])
def add_to_user_storage(message):
    user_id = str(message['message']['from']['id'])
    user_storage = UserStorage(user_id, redis_server)
    word = ' '.join(message['message']['text'].split(' ')[1:])
    out = dict.translate(word, ui='ru')['def']

    if out:
        user_storage.add_to_list(word)
        message_to_user = f'"{word}" was successfully added'
    else:
        message_to_user = f'"{word}" not found'

    bot.send_message(user_id, message_to_user, parse_mode='markdown')

@parser.command(['/del', '/d'])
def del_from_user_storage(message):
    user_id = str(message['message']['from']['id'])
    user_storage = UserStorage(user_id, redis_server)
    word = ' '.join(message['message']['text'].split(' ')[1:])

    message_to_user = f'"{word}" not in your list'
    if user_storage.del_from_list(word):
        message_to_user = f'"{word}" was successfully deleted'

    bot.send_message(user_id, message_to_user, parse_mode='markdown')

@parser.command(['/word', '/w'])
def get_random_word(message):
    user_id = str(message['message']['from']['id'])
    word = ' '.join(message['message']['text'].split(' ')[1:])
    user_storage = UserStorage(user_id, redis_server)

    user_words_list = user_storage.get_user_words_list()
    random_word = random.choice(user_words_list)
    translate_and_send(random_word, user_id)

@parser.command(['/list', '/l'])
def parse_translate(message):
    user_id = str(message['message']['from']['id'])
    user_storage = UserStorage(user_id, redis_server)

    user_words_str = ', '.join(user_storage.get_user_words_list())
    bot.send_message(user_id, user_words_str, parse_mode='markdown')

@parser.command('/debug')
def parse_debug(message):
    user_id = str(message['message']['chat']['id'])
    message_id = bot.send_message(user_id, dict_to_str(message)).message_id
    time.sleep(20)
    bot.delete_message(user_id, message_id)

@parser.command()
def parse_translate_wo_command(message):
    user_id = str(message['message']['from']['id'])
    text_to_translate = message['message']['text']
    translate_and_send(text_to_translate, user_id)

def main(message):
    parser.run(message)
