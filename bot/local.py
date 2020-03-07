import requests
import redis
import pickle
import re

from translator.classes import Translator
from translator.tools import def_to_str
from translator import add_to_user_storage

from settings import yandex_api_key


redis_server = redis.Redis(host="127.0.0.1", port=6399, db=0)
dict = Translator(yandex_api_key, redis_server)

to_translate = r'   get oUT ""+\\^% () #@^^?><           96   '

def _clear_text(text):
    return re.sub('[^A-Za-z]+', ' ', text).strip().lower()

to_translate = _clear_text(to_translate)
lang = 'en-ru'

print(to_translate)
print(len(to_translate))


# out = dict.translate(to_translate, lang=lang, ui='ru')
# print(def_to_str(out['def']))

# get_word_from_storage('124588016')


# Если слово не найдено, таки кидать в кеш, но делать кеш временным, на час-два. Для избежание дроча апи яндекса


# Добавить слово для изучение. Акутально только для пользователя добавившего слово!
# Набор из пар слово - вес

# Увеличить вес слова
# Уменьшить вес слова
