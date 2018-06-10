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
    s: str = None
    for i in range(len(data)):
        j = 0
        while j < len(data[i]):
            if s:
                if data[i][j:].find(s) == 0:
                    if len(s) == 3: j += 2
                    s = None
            else:
                for k in ('"', "'"):
                    if data[i][j] == k:
                        if j + 2 < len(data[i]) and (data[i][j + 1] == data[i][j + 2] == k):
                            s = k * 3
                        else:
                            s = k
                        break

                if not s:
                    if data[i][j] == '#':
                        data[i] = data[i][:j].rstrip()
                        break

            j += 1

        s = None

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
    def joinable(a: str, b: str, c: str) -> int:
        # считаем их уровни уровни
        levels = [0, 0, 0]
        for n, it in enumerate((a, b, c)):
            if it:
                while it[levels[n]] == ' ': levels[n] += 1

        # проверка на наличае ключевых слов
        keywords = ("class", "def", "for", "while", "if", "else", "try", "except", "finally", '@')
        a_spec = False
        for i in keywords:
            if b.lstrip().find(i) == 0:
                return 0
            elif a.lstrip().find(i) == 0:
                a_spec = True

        if not a_spec:
            return 1 if levels[0] == levels[1] else 0
        elif levels[2] < levels[1] and levels[0] < levels[1] and a.rstrip()[-1] == ':':
            return 2
        else:
            return 0

    i = 1
    while i < len(data):
        if data[i - 1][-1] == '\\':
            data[i - 1] = data[i - 1][:-1] + ' ' + data[i].lstrip()
            del data[i]
        elif data[i - 1][-1] == ',':
            data[i - 1] = data[i - 1] + ' ' + data[i].lstrip()
            del data[i]
        else:
            t = joinable(data[i - 1], data[i], data[i + 1] if i + 1 < len(data) else '')
            if t != 0:
                data[i - 1] += (';' if t == 1 else '') + data[i].lstrip()
                del data[i]
            else:
                i += 1
