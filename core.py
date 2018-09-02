from typing import List, Tuple
from bisect import insort, bisect
import re


def super_split(data: str) -> List[str]:
    """разбивает файл на строки с кодом без комментариев и превращает табуляцию в пробелы"""

    data = [i.rstrip().replace('\t', ' ') for i in data.split('\n')]

    # удаляем комментарии
    i = 0
    while i < len(data):
        mask, s = _generate_mask(data[i], 'last')
        data[i] = data[i][:len(mask)].rstrip()  # чтобы убрать комментарии в конце строки

        if not s:
            t = data[i].lstrip()
            if t:
                if t[0] in 'rbf':
                    t = t[1:]
                if t and t[0] in 'rbf':
                    t = t[1:]

                if t[:3] in ('"""', "'''"):
                    if t[:3] == t[-3:] and len(t) > 5:
                        del data[i]
                        continue

            if not data[i] or data[i].isspace():
                del data[i]
                continue
        elif data[i].lstrip().startswith(s) or (len(s) == 5 and data[i].lstrip().startswith(s[1] + s[0] + s[2:])):
            # найдено начало многострочного комментария
            while i + 1 < len(data):
                _, t = _generate_mask(data[i + 1], 'last')
                del data[i + 1]

                if not t:
                    del data[i]
                    break

            continue

        i += 1

    _generate_mask.LAST_S = None
    return data


def del_spaces(data: List[str]):
    """удаляем лишние пробелы"""

    def process(s: str) -> str:
        """
        Удаляет лишние пробелы из строки

        :param s: строка, в которой надо удалить лишние пробелы
        :return: строка без пробелов
        """

        words = [i for i in s.split(' ') if i]  # фрагменты текста без пробелов
        res = words[0]

        for i in range(1, len(words)):
            if (words[i - 1][-1].isalnum() or words[i - 1][-1] == '_')\
                    and (words[i][0].isalnum() or words[i][0] == '_'):
                res += ' '
            res += words[i]

        return res

    for i in range(len(data)):
        assert data[i]

        # ищем уровень записи
        level = 0
        while data[i][level] == ' ':
            level += 1
        data[i] = data[i][level:]

        # разбиваем на фрагменты и удаляем пробелы вне строк
        mask, _ = _generate_mask(data[i])
        blocks = []  # фрагменты строки, где либо всё в строке либо нет
        last_block_end = 0
        j = 0
        while j < len(mask):
            # ищем границу со строкой
            j += 1
            while j < len(mask) and mask[j - 1] == mask[j]:
                j += 1

            blocks.append(data[i][last_block_end: j])
            last_block_end = j

            if not mask[j - 1]:  # если фрагмент не в строке
                blocks[-1] = process(blocks[-1])  # удаляем лишние пробелы в фрагменте

        # получаем результат
        data[i] = ' ' * level + ''.join(blocks)


def update_multiline_strings(data: List[str]):
    """многострочные строки соединяет в одну линию с помощью добавления '\n'"""

    def unfs(string: str) -> Tuple[str, str]:
        """
        превращает строки типа f't e x {value(:.*?)?} t' в строки типа 't e x {(:.*?)?} t'.format(value)

        :return: обработанная строка и дополнительная строка с методом format,
        которая не должна попасть в eval тк содержит переменные
        """

        # удаляем обозначение f-строки
        assert (string[0] == 'f') ^ (string[1] == 'f')
        string = string.replace('f', '', 1)

        reg = re.compile(r'{(?![:}])(?P<var_name>.*?)(?::.*?)?}')
        match = reg.search(string)

        if not match:
            return string, ''  # Вернём всё как есть
        else:
            postfix = '.format('

        # проходя по всем позициям будем убирать значения и переносить их в аргументы метода format
        while match:
            string = string[:match.start('var_name')] + string[match.end('var_name'):]
            postfix += match.group('var_name') + ','
            match = reg.search(string)

        return string, postfix[:-1] + ')'

    i = 0  # номер строки на которой мы находимся
    while i < len(data):
        mask, s = _generate_mask(data[i])

        if s:  # если строка многострочная
            assert len(s) >= 3 and i + 1 < len(data)

            # ищем закрывающие симвалы
            begin = data[i].find(s)  # начало строки

            j = i + 1
            mask, _ = _generate_mask(data[j], s, False)

            while all(mask):  # пока все смвалы находятся в литерале строки
                j += 1
                mask, _ = _generate_mask(data[j], s, False)

            end = mask.index(False) + 3  # конец закрывающих симвалов

            # получаем итоговую строку
            string = data[i][begin:] + '\n' + '\n'.join(data[i + 1: j]) + '\n' + data[j][:end]
            if 'f' in s:  # f-string
                string, postfix = unfs(string)
            else:
                postfix = ''  # тут то, что не должно попасть в eval и находится в конце пр: .format(...) для f-строк
            string = repr(eval(string)) + postfix

            # удаляем строки между i и j
            for _ in range(1, j - i):
                del data[i + 1]

            # удаляем старую строку и обьединяем строки с новой
            data[i] = data[i][:begin] + string + data[i + 1][end:]
            del data[i + 1]
        else:
            assert not s
            i += 1


def optimize_str_count(data: List[str]):
    """обьединяет строки если это возможно"""

    def is_joining(a: str, b: str, c: str) -> int:
        """
        :param a: трока к которой мы хотим потсоединить b
        :param b: подсоединяемая строка
        :param c: строка после подсоединяемой для понимания контекста
        :return: 0 если соединить нельзя. 1 если можно соединить через ';'. 2 если можно соединить через пробел.
        3 если можно просто соединить без всего.
        """

        # проверка на вхождение в литералы коллекций и прочую фигню(например параметры функций)
        if a[-1] in "({[,":
            return 3
        if b and b.lstrip()[0] in ")]}":
            return 3

        # проверка на логические вырожения
        if len(a) >= 3:
            if (a[-2:] == "or" and not a[-3].isalnum() and a[-3] != '_')\
                    or (a[-3:] == "and" and not a[-4].isalnum() and a[-4] != '_'):
                return 2

        # считаем их уровни уровни
        levels = [0, 0, 0]  # количество пробелов перед строками a, b, c
        for n, it in enumerate((a, b, c)):
            if it:
                while it[levels[n]] == ' ':
                    levels[n] += 1

        # проверка на наличае ключевых слов
        keywords = ("class", "def", "for", "while", "if", "elif", "else", "try", "except", "finally", '@')
        a_spec = False  # является ли a ключевым словом
        for i in keywords:
            if b.lstrip().startswith(i):
                return 0
            elif a.lstrip().startswith(i):
                a_spec = True

        if not a_spec:  # если в a - ключевое слово
            return int(levels[0] == levels[1])
        elif levels[2] < levels[1] and levels[0] < levels[1] and a.rstrip()[-1] == ':':
            # b - единственная строка в блоке кода
            return 3
        else:
            return 0

    i = 1  # номер строки
    while i < len(data):
        assert data[i]

        if data[i - 1][-1] == '\\':  # если строка под номером i это продолжение предыдущей
            data[i - 1] = data[i - 1][:-1] + ' ' + data[i].lstrip()
            del data[i]
        else:
            t = is_joining(data[i - 1], data[i], data[i + 1] if i + 1 < len(data) else '')
            if t != 0:
                data[i - 1] += (';', ' ', '')[t - 1] + data[i].lstrip()
                del data[i]
            else:
                i += 1


def _generate_mask(arg: str, s: str=None, as_f_string=True) -> Tuple[List[bool], str]:
    """
    :param arg: строка для генерации маски
    :param s: строка из симвала(ов), открывающих строку. (передавать если
    эта строка в многострочной строке)
    :return: список, где True соответствует элементам не в комментарии и
    строку, равную симвалам незакрытой строки.
    """

    if s == 'last':
        s = _generate_mask.LAST_S

    is_raw = s and 'r' in s
    is_binary = s and 'b' in s
    is_format = s and 'f' in s
    s = s and ''.join(filter(lambda x: x in '\'"', s))  # удаляем из s все симвалы кроме ' и "

    res = [False for _ in range(len(arg))]  # маска, которую возвращаем
    i = 0
    while i < len(arg):
        if s:
            k = 0  # количество знаков r'\' перед симвалом
            while i - k > 0 and arg[i - k - 1] == '\\':
                k += 1

            if k % 2 == 0:  # если симвал arg[i] не экранирован
                if arg[i: i + 3].startswith(s):  # если на позиции i закрытие строки
                    i += len(s)
                    s = is_raw = is_binary = is_format = None
                    continue

                if as_f_string and is_format and arg[i] == '{':
                    # обозначим найденое вырожение не как часть строки
                    res[i] = True

                    ss = 0  # количество симвалав открытой строки
                    n = 0  # количество незакрытых фигурных скобочек
                    while i < len(arg):
                        i += 1

                        if arg[i] in ('"', "'"):
                            assert arg[i] not in s

                            if ss:
                                if ss == 3:
                                    if arg[i + 1] == arg[i + 2] == arg[i]:
                                        ss = 0
                                        i += 2
                                    else:
                                        res[i] = True
                                else:
                                    assert ss == 1
                                    ss = 0
                            else:
                                if arg[i + 1] == arg[i + 2] == arg[i]:
                                    ss = 3
                                    i += 2
                                else:
                                    ss = 1
                        elif ss:
                            res[i] = True
                        elif arg[i] == '}':
                            if n == 0:
                                res[i] = True
                                break
                            else:
                                n -= 1
                        elif arg[i] == '{':
                            n += 1

        elif arg[i] in ('"', "'"):
            if i > 0 and arg[i - 1].isalpha():
                is_raw = arg[i - 1] == 'r'
                is_binary = arg[i - 1] == 'b'
                is_format = arg[i - 1] == 'f'

                if i > 1 and arg[i - 2].isalpha():
                    is_raw = is_raw or arg[i - 2] == 'r'
                    is_binary = is_binary or arg[i - 2] == 'b'
                    is_format = is_format or arg[i - 2] == 'f'
            else:
                is_binary = is_format = is_raw = False
            s = arg[i]

            if i + 2 < len(arg) and arg[i] == arg[i + 1] == arg[i + 2]:
                i += 3
                s *= 3
            else:
                i += 1

            continue
        elif arg[i] == '#':  # не делаем маску на комментарии
            res = res[:i]
            break

        if s:
            res[i] = True

        i += 1

    assert (s is None) ^ (is_raw is not None and is_binary is not None and is_format is not None)
    assert not is_binary or not is_format

    _generate_mask.LAST_S = s = f"{'r'*is_raw}{'f'*is_format}{'b'*is_binary}{s}" if s else None
    return res, s


_generate_mask.LAST_S: str = None


def _count_left_spaces(line: str) -> int:
    """считает количество пробелов в начале строки"""
    res = 0
    while res < len(line) and line[res] == ' ':
        res += 1
    return res


def minimize_left_space(data):
    """убирает лишние пробелы слева"""
    space_counts = []  # все варианты количества пробелов слева

    # заполняем space_counts
    for i in data:
        c = _count_left_spaces(i)

        if c and c not in space_counts:
            insort(space_counts, c)  # вставка в отсортированный масссив

    if space_counts:
        # заменяем количество пробелов в строках на индекс в space_counts + 1
        for i in range(len(data)):
            c = _count_left_spaces(data[i])

            if c:
                data[i] = ' '*bisect(space_counts, c) + data[i][c:]
