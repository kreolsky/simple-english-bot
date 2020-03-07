import requests
import redis
import pickle
import re


# TODO Вынести яндекс переводчик отдельным обьектом для заменяемости

class Translator(object):
    def __init__(self, yandex_api_key, redis_server):
        self._yandex_api_key = yandex_api_key
        self._redis_server = redis_server

    def _api(self, params):
        params['key'] = self._yandex_api_key
        url = f'https://dictionary.yandex.net/api/v1/dicservice.json/lookup'

        return requests.get(url, params=params).json()

    def _get_from_cache(self, lang, text):
        key = f'{lang}:{text}'
        return self._redis_server.get(key)

    def _put_to_cache(self, lang, text, article):
        key = f'{lang}:{text}'
        return self._redis_server.set(key, article)

    def _yandex_translate(self, text, lang, ui):
        params = {
            'lang': lang,
            'text': text,
            'ui': ui,
            'flags': 4
        }

        out = self._api(params)
        return out

    def _clear_text(self, text):
        return re.sub('[^A-Za-z]+', ' ', text).strip().lower()

    def translate(self, text, lang='en-ru', ui='en'):
        text = self._clear_text(text)

        cache = self._get_from_cache(lang, text)
        if cache:
            return pickle.loads(cache)

        out = self._yandex_translate(text, lang, ui)
        if out['def']:
            self._put_to_cache(lang, text, pickle.dumps(out))

        return out


class UserStorage(object):
    def __init__(self, user_id, redis_server):
        self._user_key = f'user:{user_id}'
        self._redis_server = redis_server

    def get_user_words_list(self, group='base'):
        user_key = f'{self._user_key}:{group}'.encode()
        user_words_list = self._redis_server.get(user_key) or pickle.dumps(['hello'])

        return pickle.loads(user_words_list)

    def _update_user_words_list(self, group, user_words_list):
        user_key = f'{self._user_key}:{group}'.encode()
        user_words_list = pickle.dumps(user_words_list)

        self._redis_server.set(user_key, user_words_list)
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
        if function in self.handlers:
            self.handlers[function].update(handler_data_dict)
        else:
            self.handlers[function] = handler_data_dict

    def _command(self, handler_type, handler_data):
        if type(handler_data) == str:
            handler_data = [handler_data, ]

        def decorator(function):
            self._add_to_handler_list(function, {handler_type: handler_data})

            return function
            # В классических декораторах тут должен быть wrapper
        return decorator

    def command(self, command=None):
        return self._command(handler_type='command', handler_data=command)

    def permission(self, permission):
        return self._command(handler_type='permission', handler_data=permission)

    def run(self, message):
        for func, handler_data in self.handlers.items():

            user_id = str(message['message']['from']['id'])
            message_command = message['message']['text'].split(' ')[0]
            message_text = message['message']['text']

            permission = 'permission' not in handler_data or user_id in handler_data['permission']
            command = not handler_data['command'] or message_command in handler_data['command']

            if command and permission:
                func(message)
                break
