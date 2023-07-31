import re


def list_join(list_data, sep):
    return f'{sep} '.join([i['text'] for i in list_data])

def clear_text(text):
    return re.sub('[^A-Za-z]+', ' ', text).strip().lower()

def def_to_str(income: list) -> str:
    out = ''
    for item in income:
        ts = f"[[{item['ts']}]] " if 'ts' in item else "" #  Произношение
        pos = f"_{item['pos']}_" if 'pos' in item else "" #  Часть речи
        fl = f"({item['fl']})" if 'fl' in item else "" #  Формы глагола

        out += f"*{item['text']}* {fl} {ts}{pos}\n"

        for i, text in enumerate(item['tr'], start=1):
            mean = f"({list_join(text['mean'], ',')})" if 'mean' in text else "" # Синонимы
            out += f"{i}. {text['text']} {mean}\n"

            # Примеры
            if 'ex' in text:
                out += '\n'.join([f"   {ex['text']} - {list_join(ex['tr'], '.')}" for ex in text['ex']])
                out += '\n'

        out += '\n'

    return out

def dict_to_str(source, tab='', count=0):
    output = ''

    if not isinstance(source, dict):
        return source

    for key, value in source.items():
        end = ''
        if isinstance(value, dict):
            count += 1
            value = dict_to_str(value, ' ' * 4, count)
            end = '\n'
            count -= 1

        output += f'{tab * count}{str(key)}: {end}{str(value)}\n'

    return output[:-1]

# Если есть синонимы 'mean' их нужно перечислить через запятую
# Если есть примеры 'ex' их нужно перечислить
