from typing import List, Tuple


# разбивает файл на строки с кодом без комментариев в конце и превращает табуляцию в пробелы
def super_split(data: str) -> List[str]:
    data = [i.rstrip().replace('\t', ' ') for i in data.replace('\\\n', '').split('\n')]

    # удаляем комментарии
    i = 0
    while i < len(data):
        mask, s = _generate_mask(data[i], 'last')
        data[i] = data[i][:len(mask)].rstrip()  # чтобы убрать комментарии в конце строки

        if not s:
            t = data[i].lstrip()
            if t:
                if t[0] in 'rbf': t = t[1:]
                if t and t[0] in 'rbf': t = t[1:]

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


# удаляем пробелы между операторами
def del_spaces(data: List[str]):
    def process(s: str) -> str:
        """
        Удаляет лишние пробелы из строки.
        :param s: строка, в которой надо удалить лишние пробелы
        :return: строка без пробелов
        """

        blocks = [i for i in s.split(' ') if i]
        res = blocks[0]

        for i in range(1, len(blocks)):
            if (blocks[i - 1][-1].isalnum() or blocks[i - 1][-1] == '_')\
                    and (blocks[i][0].isalnum() or blocks[i][0] == '_'):
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
        mask, _ = _generate_mask(data[i])
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
    i = 0  # номер строки на которой мы находимся
    while i < len(data):
        mask, s = _generate_mask(data[i])

        if s and len(s) >= 3 and i + 1 < len(data):  # если есть многострочная строка
            # ищем закрывающие симвалы
            begin = data[i].find(s)  # начало строки

            g = i + 1
            mask, _ = _generate_mask(data[g], s)

            while all(mask):  # пока все исмвалы находятся в коментарии
                g += 1
                mask, _ = _generate_mask(data[g], s)

            end = mask.index(False) + 3  # конец закрывающих симвалов

            # получаем итоговую строку
            string = eval(
                data[i][begin:] + ('\n' if len(data[i]) == begin + len(s) else '')
                + '\n'.join([data[i] for i in range(i + 1, g)]) + '\n' + data[g][:end]
                         )
            assert type(string) in (str, bytes)

            # удаляем строки между i и g
            for _ in range(1, g - i):
                del data[i + 1]

            # удаляем старую строку и обьединяем строки с новой
            data[i] = data[i][:begin] + repr(string) + data[i + 1][end:]
            del data[i + 1]
        else:
            assert not s
            i += 1


# обьединяет строки если это возможно
def optimize_str_count(data: List[str]):
    def joinable(a: str, b: str, c: str) -> int:
        """
        :param a: трока к которой мы хотим потсоединить b
        :param b: подсоединяемая строка
        :param c: строка после подсоединяемой для понимания контекста
        :return: 0 если соединить нельзя. 1 если можно соединить через ';'. 2 если можно соединить через пробел.
        3 если можно просто соединить без всего.
        """

        # проверка на вхождение в литералы коллекций и прочую фигню(например параметры функций)
        if a[-1] in "({[,": return 3
        if b and b.lstrip()[0] in ")]}": return 3

        # проверка на логические вырожения
        if len(a) >= 2:
            if a[-2:] == "or" or (len(a) >= 3 and a[-3:] == "and"):
                return 2

        # считаем их уровни уровни
        levels = [0, 0, 0]
        for n, it in enumerate((a, b, c)):
            if it:
                while it[levels[n]] == ' ': levels[n] += 1

        # проверка на наличае ключевых слов
        keywords = ("class", "def", "for", "while", "if", "else", "try", "except", "finally", '@')
        a_spec = False
        for i in keywords:
            if b.lstrip().startswith(i):
                return 0
            elif a.lstrip().startswith(i):
                a_spec = True

        if not a_spec:
            return int(levels[0] == levels[1])
        elif levels[2] < levels[1] and levels[0] < levels[1] and a.rstrip()[-1] == ':':
            return 3
        else:
            return 0

    i = 1
    while i < len(data):
        assert data[i]
        if data[i - 1][-1] == '\\':
            data[i - 1] = data[i - 1][:-1] + ' ' + data[i].lstrip()
            del data[i]
        elif data[i - 1][-1] == ',':
            data[i - 1] = data[i - 1] + ' ' + data[i].lstrip()
            del data[i]
        else:
            t = joinable(data[i - 1], data[i], data[i + 1] if i + 1 < len(data) else '')
            if t != 0:
                data[i - 1] += (';' if t == 1 else (' ' if t == 2 else '')) + data[i].lstrip()
                del data[i]
            else:
                i += 1


def _generate_mask(arg: str, s: str=None) -> Tuple[List[bool], str]:
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
    s = s and ''.join(filter(lambda x: x in '\'"', s))

    res = [False for _ in range(len(arg))]
    i = 0
    while i < len(arg):
        if s:
            k = 0  # количество знаков r'\' перед симвалом
            while i - k > 0 and arg[i - k - 1] == '\\': k += 1

            if k % 2 == 0:
                if arg[i: i + 3].startswith(s):
                    i += len(s)
                    s = is_raw = is_binary = is_format = None
                    continue
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
        elif arg[i] == '#':
            res = res[:i]
            break

        if s:
            res[i] = True

        i += 1

    assert (s is None) ^ (is_raw is not None and is_binary is not None and is_format is not None)
    assert not is_binary or not is_format

    _generate_mask.LAST_S = s = 'r'*int(is_raw) + 'f'*int(is_format) + 'b'*int(is_binary) + s if s else None
    return res, s


_generate_mask.LAST_S: str = None
