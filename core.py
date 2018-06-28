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
                            j += 2
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
    def generate_mask(arg: str) -> List[bool]:
        """
        :param arg: строка для генерации маски
        :return: список, где True соответствует элементам не в комментарии
        """

        res = [False for _ in range(len(arg))]
        i = 0
        s = None  # строка из симвала(ов), открывающих строку
        while i < len(arg):
            if s:
                if arg[i: i + 3].find(s) == 0:
                    i += len(s)
                    s = None
                    continue
            elif arg[i] in ('"', "'"):
                s = arg[i]

                if i + 2 < len(arg) and arg[i] == arg[i + 1] == arg[i + 2]:
                    i += 3
                    s *= 3
                else:
                    i += 1

                continue

            if s:
                res[i] = True

            i += 1

        return res

    def process(s: str) -> str:
        """
        Удаляет лишние пробелы из строки.
        :param s: строка, в которой надо удалить лишние пробелы
        :return: строка без пробелов
        """

        blocks = [i for i in s.split(' ') if i]
        res = blocks[0]

        for i in range(1, len(blocks)):
            if (blocks[i - 1][-1].isalnum() or blocks[i - 1][-1] == '_') and (blocks[i][0].isalnum() or blocks[i][0] == '_'):
                res += ' '
            res += blocks[i]

        return res

    for i in range(len(data)):
        assert data[i]

        # ищем уровень записи
        level = 0
        while data[i][level] == ' ': level += 1
        data[i] = data[i][level:]

        # разбиваем на фрагменты и удаляем пробелы вне строк
        mask = generate_mask(data[i])
        blocks = []
        last_block_end = 0
        j = 0
        while j < len(mask):
            j += 1
            while j < len(mask) and mask[j - 1] == mask[j]: j += 1
            blocks.append(data[i][last_block_end: j])
            if not mask[j - 1]: blocks[-1] = process(blocks[-1])
            last_block_end = j

        # получаем результат
        data[i] = ' ' * level + ''.join(blocks)


# многострочные строки соединяет в одну линию с помощью добавления '\n'
def update_multiline_strings(data: List[str]):
    s: str = None  # симвал[ы] начала комментария (храним тк они же его и закончат)
    i = 0  # номер строки на которой мы находимся
    t = 0  # содержит либо 0 либо ту позицию, на которой мы остановились если была добавлена строка в конец передыдущей
    while i < len(data):
        j = t  # номер симвала? который мы рассматриваем
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
                            j += 2
                        else:
                            s = k
                        break

            j += 1

        if s and len(s) == 3 and i + 1 < len(data):
            if data[i].rstrip()[-3:] == s:
                t = len(data[i]) + 5
                data[i] = data[i][:-3] + r"'\n'+" + s + data[i + 1]
            else:
                t = len(data[i]) + 12
                data[i] += s + r"+'\n'+" + s + data[i + 1]
            del data[i + 1]
        else:
            i += 1
            t = 0


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
