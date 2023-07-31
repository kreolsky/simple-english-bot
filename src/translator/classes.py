import requests
import redis
import re
import uuid
import time
import pickle

from settings import yandex_not_found_cache_sec
from settings import log_chunk_size_sec
# TODO Вынести яндекс переводчик отдельным обьектом для заменяемости

class Translator(object):
    def __init__(self, yandex_api_key, cache_server):
        self._yandex_api_key = yandex_api_key
        self._cache_server = cache_server

    def _api(self, params):
        params['key'] = self._yandex_api_key
        url = f'https://dictionary.yandex.net/api/v1/dicservice.json/lookup'

        return requests.get(url, params=params).json()

    def _get_from_cache(self, lang, text):
        key = f'{lang}:{text}'
        return self._cache_server.get(key)

    def _put_to_cache(self, lang, text, article, ttl=None):
        # ttl -- time to live

        key = f'{lang}:{text}'
        self._cache_server.set(key, article)

        if ttl:
            self._cache_server.expire(key, ttl)

    def _yandex_translate(self, text, lang, ui):
        params = {
            'lang': lang,
            'text': text,
            'ui': ui,
            'flags': 4
        }

        out = self._api(params)
        return out

    def translate(self, text, lang='en-ru', ui='en'):
        log_data = {
            'status': 'not_found',
            'storage': 'cache',
            'provider': '',
            }

        cache = self._get_from_cache(lang, text)
        if cache:
            out = pickle.loads(cache)
            if out['def']:
                log_data['status'] = 'success'

            if 'provider' in out:
                log_data['provider'] = out['provider']

            out['log'] = log_data
            return out

        out = self._yandex_translate(text, lang, ui)
        log_data['storage'] = 'internet'
        log_data['provider'] = 'yandex'
        out['provider'] = 'yandex' # Добавить в кеш данные откуда взята словарная статья

        if out['def']:
            self._put_to_cache(lang, text, pickle.dumps(out))
            log_data['status'] = 'success'
        else:
            self._put_to_cache(lang, text, pickle.dumps(out), ttl=yandex_not_found_cache_sec)

        # Добавить к ответу метадату
        out['log'] = log_data
        return out


class UserStorage(object):
    def __init__(self, user_id, cache_server):
        self._user_key = f'user:{user_id}'
        self._cache_server = cache_server

    def get_user_words_list(self, group='base'):
        user_key = f'{self._user_key}:{group}'.encode()
        user_words_list = self._cache_server.get(user_key) or pickle.dumps(['hello'])

        return pickle.loads(user_words_list)

    def _update_user_words_list(self, group, user_words_list):
        user_key = f'{self._user_key}:{group}'.encode()
        user_words_list = pickle.dumps(user_words_list)

        self._cache_server.set(user_key, user_words_list)
        return True

    def add_to_list(self, word, group='base'):
        user_words_list = self.get_user_words_list(group)
        user_words_list.append(word)

        return self._update_user_words_list(group, user_words_list)

    def del_from_list(self, word, group='base'):
        user_words_list = self.get_user_words_list(group)
        if word not in user_words_list:
            return False

        user_words_list.remove(word)
        return self._update_user_words_list(group, user_words_list)


class MessageHandler():
    def __init__(self):
        self.handlers = {}

    def _add_to_handler_list(self, function, handler_data_dict):
        self.handlers.setdefault(function, {}).update(handler_data_dict)

    def _command(self, handler_type, handler_data):
        if isinstance(handler_data, str):
            handler_data = [handler_data]

        def decorator(function):
            self._add_to_handler_list(function, {handler_type: handler_data})
            return function
            # В классических декораторах тут должен быть wrapper
        return decorator

    def command(self, command=None):
        return self._command('command', command)

    def permission(self, permission=None):
        return self._command('permission', permission)

    def run(self, message):
        user_id = str(message['message']['from']['id'])
        message_command = message['message']['text'].split(' ')[0]
        message_text = message['message']['text']

        for func, handler_data in self.handlers.items():
            permissions = handler_data.get('permission', [])
            commands = handler_data.get('command', [])

            permission = not permissions or user_id in permissions
            command = not commands or message_command in commands

            if command and permission:
                func(message)
                break


class Logger():
    def __init__(self, log_server, chunk_size=log_chunk_size_sec):
        self._log_server = log_server
        self._chunk_size = chunk_size

    def set_chunk_size(self, chunk_size):
        self._chunk_size = chunk_size

    def add(self, log_data):
        chunk_name = int(time.time() // self._chunk_size * self._chunk_size)
        key = str(uuid.uuid4())
        value = pickle.dumps(log_data)

        self._log_server.hset(chunk_name, key, value)

    def get_all_chunks(self):
        keys = self._log_server.keys()
        for key in keys:
            yield key, self._log_server.hgetall(key)

    def drop(self):
        keys = self._log_server.keys()
        for key in keys:
            self._log_server.delete(key)
