import os
import time
import datetime
import random
import pickle
import json
import zipfile

from redis import Redis
from telebot import TeleBot

from .classes import MessageHandler
from .classes import Translator
from .classes import UserStorage
from .classes import Logger
from . import tools

from settings import telebot_token
from settings import yandex_api_key
from settings import allow_users

redis_cache_server = Redis(host='redis', db=0)
redis_log_server = Redis(host='redis', db=15)

bot = TeleBot(telebot_token)
parser = MessageHandler()
translator = Translator(yandex_api_key, redis_cache_server)
logger = Logger(redis_log_server)


@parser.command('/about')
def get_user_info(message):
    user_id = str(message['message']['chat']['id'])
    message_id = bot.send_message(user_id, tools.dict_to_str(message)).message_id
    time.sleep(20)
    bot.delete_message(user_id, message_id)


@parser.permission(allow_users)
@parser.command('/debug')
def save_logs_to_file(message):
    out = {}
    for key, chunk in logger.get_all_chunks():
        key = key.decode()
        out[key] = {k.decode(): pickle.loads(v) for k, v in chunk.items()}

    filename = f'debug-{int(time.time())}.json'
    with open(filename, 'w') as file:
        json.dump(out, file, indent=2, ensure_ascii=False)

    zip_filename = f'{filename}.zip'
    with zipfile.ZipFile(zip_filename, 'w', compression=zipfile.ZIP_DEFLATED) as zipf:
        zipf.write(filename)

    user_id = str(message['message']['chat']['id'])
    with open(zip_filename, 'rb') as file:
        bot.send_document(user_id, file)

    os.remove(filename)
    os.remove(zip_filename)

# @parser.permission(allow_users)
# @parser.command('/drop')
# def drop_log_storage(message):
#     logger.drop()


@parser.command()
def translate_word(message):
    user_id = message['message']['from']['id']
    chat_id = message['message']['chat']['id']
    request = message['message']['text']
    text_to_translate = tools.clear_text(request)

    log_data = {
        'ts': str(datetime.datetime.now()),
        'event_name': 'word_translate',
        'status': '',
        'user': user_id,
        'channel': 'telegram',
        'message': {
            'request': request,
            'text_to_translate': text_to_translate,
            'provider': '',
            'storage': '',
            'extra': {
                'telegram': message['message']
                }
            }
        }

    if text_to_translate:
        result = translator.translate(text_to_translate, ui='ru')
        log_data['status'] = result['log']['status']
        log_data['message']['storage'] = result['log']['storage']
        log_data['message']['provider'] = result['log']['provider']

        result_def = f'"{text_to_translate}" not found'
        if result['def']:
            result_def = tools.def_to_str(result['def'])

        bot.send_message(chat_id, result_def, parse_mode='markdown')

    else:
        log_data['status'] = 'wrong_request'

    logger.add(log_data)


# @parser.command(['/add', '/a'])
# def add_to_user_storage(message):
#     user_id = str(message['message']['from']['id'])
#     chat_id = str(message['message']['chat']['id'])
#     word = ' '.join(message['message']['text'].split(' ')[1:])
#
#     user_storage = UserStorage(user_id, redis_cache_server)
#
#     out = translator.translate(word, ui='ru')
#     is_success = 'def' in out and out['def']
#
#     if is_success:
#         user_storage.add_to_list(word)
#         message_to_user = f'"{word}" was successfully added'
#     else:
#         message_to_user = f'"{word}" not found'
#
#     bot.send_message(user_id, message_to_user, parse_mode='markdown')
#
# @parser.command(['/del', '/d'])
# def del_from_user_storage(message):
#     user_id = str(message['message']['from']['id'])
#     word = ' '.join(message['message']['text'].split(' ')[1:])
#     user_storage = UserStorage(user_id, redis_cache_server)
#
#     message_to_user = f'"{word}" not in your list'
#     if user_storage.del_from_list(word):
#         message_to_user = f'"{word}" was successfully deleted'
#
#     bot.send_message(user_id, message_to_user, parse_mode='markdown')
#
# @parser.command(['/word', '/w'])
# def get_random_word_from_storage(message):
#     user_id = str(message['message']['from']['id'])
#     chat_id = str(message['message']['chat']['id'])
#     user_storage = UserStorage(user_id, redis_cache_server)
#
#     user_words_list = user_storage.get_user_words_list()
#     random_word = random.choice(user_words_list)
#     translate_and_send(random_word, user_id, chat_id)
#
# @parser.command(['/list', '/l'])
# def get_user_list(message):
#     user_id = str(message['message']['from']['id'])
#     user_storage = UserStorage(user_id, redis_cache_server)
#
#     user_words_str = ', '.join(user_storage.get_user_words_list())
#     bot.send_message(user_id, user_words_str, parse_mode='markdown')

def main(message):
    parser.run(message)
