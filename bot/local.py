import requests
import redis
import pickle
import re
import uuid

from translator.classes import Translator
from translator.classes import Logger

from translator.tools import def_to_str

from settings import yandex_api_key


redis_cache_server = redis.Redis(host="127.0.0.1", port=6399, db=0)
redis_log_server = redis.Redis(host="127.0.0.1", port=6399, db=15)

logger = Logger(redis_log_server)
dict = Translator(yandex_api_key, redis_cache_server)

to_translate = r'   purchasegg ""+\\^% () #@^^?><           96   '

def _clear_text(text):
    return re.sub('[^A-Za-z]+', ' ', text).strip().lower()

to_translate = _clear_text(to_translate)
lang = 'en-ru'

# print(to_translate)
# print(len(to_translate))

out = dict.translate(to_translate, lang=lang, ui='ru')
print(out, end='\n\n')
print(out['log'], end='\n\n')

# if 'def' in out:
#     print(def_to_str(out['def']))

key = str(uuid.uuid4())
value = def_to_str(out['def'])


for chunk in logger.get_all_chunks():
    print(chunk)


# redis_log_server.hset('test_hset', key, value)
# redis_log_server.expire('test_hset', 5)


# Если слово не найдено, таки кидать в кеш, но делать кеш временным, на час-два. Для избежание дроча апи яндекса

# Добавить слово для изучение. Акутально только для пользователя добавившего слово!
# Набор из пар слово - вес

# Увеличить вес слова
# Уменьшить вес слова
