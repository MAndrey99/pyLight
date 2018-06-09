import re
from typing import List


# убираем многострочные комментарии
def del_multiline_comments(data: str) -> str:
    for i in ('"""', "'''"):
        # удаляем с самого начала
        reg = re.compile(r"\s*" + i + r"(?:(?!" + i + r").|\n)*?" + i)
        m = reg.match(data)
        while m:
            data = data[m.end() + 1:]
            m = reg.match(data)

        # удаляем в остальных местах
        reg = re.compile(r"(?<!\\)\n\s*" + i + r"(?:(?!" + i + ").|\n)*?" + i)
        m = reg.search(data)
        while m:
            data = data[:m.start()] + data[m.end():]
            m = reg.search(data)

    return data


# разбивает файл на строки с кодом без комментариев в конце и превращает табуляцию в пробелы
def super_split(data: str) -> List[str]:
    reg = re.compile(r"^\s*#.*")  # вся строка-комментарий
    data = [i.replace('\t', ' ').rstrip() for i in data.split('\n') if i and not reg.match(i)]

    # удаляем комментарии в конце
    for i in range(len(data)):
        n = data[i].find('#')
        if n != -1: data[i] = data[i][:n].rstrip()

    return data


# удаляем пробелы между операторами
def del_spaces(data: List[str]):
    for i in range(len(data)):
        # ищем уровень записи
        level = 0
        while data[i][level] == ' ': level += 1
        data[i] = data[i][level:]

        # удаляем повторные пробелы
        while '  ' in data[i]: data[i] = data[i].replace('  ', ' ')

        # удаляем пробелы
        t = [i for i in data[i].split(' ') if i]
        data[i] = ' ' * level + t[0]
        for j in range(1, len(t)):
            if (t[j - 1][-1].isalnum() or t[j - 1][-1] == '_') and (t[j][0].isalnum() or t[j][0] == '_'):
                data[i] += ' '
            data[i] += t[j]


# обьединяет строки если это возможно
def optimize_str_count(data: List[str]):
    def joinable(a: str, b: str) -> bool:
        # проверка на разные уровни
        i = 0
        while a[i] == b[i] == ' ': i += 1
        if a[i] == ' ' or b[i] == ' ': return False

        # проверка на наличае ключевых слов
        keywords = ("class", "lambda", "def", "for", "while", "if", "else", "try", "except", "finally", '@')
        for i in keywords:
            if a.find(i) != -1 or b.find(i) != -1:
                return False

        return True

    i = 1
    while i < len(data):
        if data[i - 1][-1] == '\\':
            data[i - 1] = data[i - 1][:-1] + ' ' + data[i].lstrip()
            del data[i]
        elif data[i - 1][-1] == ',':
            data[i - 1] = data[i - 1] + ' ' + data[i].lstrip()
            del data[i]
        elif joinable(data[i - 1], data[i]):
            data[i - 1] += ';' + data[i].lstrip()
            del data[i]
        else:
            i += 1
