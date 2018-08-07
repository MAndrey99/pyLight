import re
from typing import List
from operator import getitem
from functools import partial
from io import StringIO

from core import _generate_mask


def del_asserts(data: List[str]):
    """
    заменяет все assert'ы на "pass"

    :param data: список обработанных строк кода
    """

    for i in range(len(data)):
        mask, s = _generate_mask(data[i])
        assert not s  # все строки уже немногострочны
        assert '\n' not in data[i]

        # с помощью регулярки ищем assert'ы
        reg = re.compile(r"assert [^;]+")
        match = reg.search(data[i])

        # заменяем все, что находим на pass
        while match:
            if not mask[match.start()]:
                data[i] = f'{data[i][:match.start()]}pass{data[i][match.end():]}'  # заменяем то что нашли на pass
                mask, s = _generate_mask(data[i])  # обновляем маску
                assert not s

                match = reg.search(data[i], pos=match.start() + 4)
            else:
                match = reg.search(data[i], pos=match.end())


def _convert_base(num, to_base=62) -> str:
    assert to_base < 63 and num > 0
    num = int(num)

    alphabet = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZqwertyuiopasdfghjklzxcvbnm_"
    if num < to_base:
        return alphabet[num]
    else:
        return _convert_base(num // to_base, to_base) + alphabet[num % to_base]


def delete_annotations(data: List[str]):
    """
    удаляет анотации у аргументов функций

    :param data: список обработанных строк кода
    """
    reg_var = re.compile(r"[A-Za-z_][\w_]*")  # имя переменной
    reg_annotation = re.compile(r'[A-Za-z_][\w_]*:.*')
    reg_arg_annotation = re.compile(r":(?:[A-Za-z_][\w_]*\.)*(?:[A-Za-z_][\w_]*)")

    i = 0  # номер строки кода, которую обрабатываем
    while i < len(data):
        mask, _ = _generate_mask(data[i])

        t = data[i].lstrip()
        if t.startswith('def ') or t.startswith('async def'):
            # удаляем аннотации функциии
            # ! данный метод не поддерживает функции и любые другие вырожения
            search_start = data[i].find('(') + 1

            # ищем конец функции
            t = len(data[i])
            while True:
                search_end = data[i][search_start: t].rfind('):') + search_start

                if not mask[search_end]:
                    break

                t = search_end - 2
            del t

            mask, _ = _generate_mask(data[i])

            # в цикле находим и удаляем все анотации
            while True:
                match = reg_arg_annotation.search(data[i], pos=search_start, endpos=search_end)

                if not match:
                    break

                if not mask[match.start()]:  # если найденный фрагмент не в комментарии
                    data[i] = data[i][:match.start()] + data[i][match.end():]
                    mask = mask[:match.start()] + mask[match.end():]
                    search_end -= match.end() - match.start()

                    if data[i][match.start()] == '[':
                        o_count = 1  # количество незакрытых кв. скобочек
                        p = match.start() + 1  # номер рассматриеваемого симвала

                        while o_count > 0 and p < len(data[i]):
                            if not mask[p]:
                                if data[i][p] == ']':
                                    o_count -= 1
                                elif data[i][p] == '[':
                                    o_count += 1

                            p += 1
                        assert o_count == 0

                        # удаляем найденые скобочки
                        data[i] = data[i][:match.start()] + data[i][p:]
                        mask = mask[:match.start()] + mask[p:]
                        search_end -= p - match.start()
                else:
                    search_start = match.end()
        elif reg_annotation.match(t):
            def get_colon_pos() -> int:
                """возвращает положения симвала ':' пред аннотацией или -1"""

                n = 0
                colon_pos = -1

                while n < len(data[i]):
                    while data[i][n] != ':' and n < len(data[i]):
                        n += 1

                    var_name = data[i][colon_pos + 1: n]
                    colon_pos = n

                    if var_name not in ['try', 'else', 'finally'] and reg_var.match(var_name):
                        break

                    if not reg_annotation.match(data[i][colon_pos + 1:]):
                        return -1

                    n += 1

                return colon_pos

            eq_pos = None
            colon_pos = get_colon_pos()

            if colon_pos != -1:
                # ищем знак равно так чтобы не среагировать на операторы <=, !=, == и тд., а так же на строки
                for j in range(colon_pos, len(mask)):
                    if not mask[j]:
                        if data[i][j] == '=' and data[i][j + 1] not in '<>!=' and data[i][j - 1] not in '<>!=':
                            eq_pos = j
                            break

                # если эта строчка чисто аннотация, то её надо удалить!
                if eq_pos is None:
                    del data[i]
                    continue

                data[i] = data[i][:colon_pos] + data[i][eq_pos:]  # вырезаем саму аннотацию

        i += 1


def _arguments(definition: str, have_annotations: bool) -> List[str]:
    """
    Даёт список аргументов обьявленной функции

    :param definition: строка с обьявлением функции без пробельных симвалов в начале
    """
    assert definition.endswith('):')

    if definition.startswith('async'):
        definition = definition[6:]

    if have_annotations:
        t = [definition]
        delete_annotations(t)
        definition = t[0]  # теперь definition без аннотаций

    if '"' in definition or "'" in definition:
        # удаляем содержимое строчных литералов чтобы не мешалось
        mask, _ = _generate_mask(definition)
        t = StringIO()

        for i in range(len(mask)):
            if not mask[i]:
                t.write(definition[i])

        definition = t.getvalue()

    # вместе с =...
    with_eq = list(filter(bool, map(lambda x: x.replace('*', ''), definition[definition.find('(') + 1:-2].split(','))))
    return list(map(lambda x: x if '=' not in x else x[:x.find('=')], with_eq))  # удераем значения по умолчанию


def rename_locals(data: List[str], have_annotations=True):
    """
    переименовывает все локальные переменные в функциях

    :param have_annotations: возможно ли присудствие аннотаций функций в коде
    :param data: список обработанных строк кода
    """

    def commands(line: str):
        """разбиваем строку на выражения типа: a+=1;print(a) -> a+=1 и print(a)"""
        assert line

        line = line.lstrip()
        mask, _ = _generate_mask(line)

        begin = 0  # начало рассматривоемого вырожения
        for i in range(1, len(line)):
            if line[i] == ';' and not mask[i]:
                yield line[begin: i]
                begin = i + 1
        yield line[begin:]

    def search(var_name: str, text: str) -> re.Match:
        """ищем переменную в строке кода"""
        mask, _ = _generate_mask(text)

        while True:
            match = re.search(r"(?<!\.)\b{}\b".format(var_name), text)

            if not match:
                return None

            if mask[match.start()]:
                text = text[:match.start()] + '-'*len(match.group()) + text[match.end():]
            else:
                return match

    reg_var = re.compile(r"[A-Za-z_][\w_]*")  # имя переменной
    reg_make_vars = re.compile(r"(?:\*?[A-Za-z_][\w_]*)(?:,\*?(?:[A-Za-z_][\w_]*))*(?<!,)=.+")  # создание переменных

    i = -1
    while i + 1 < len(data):
        i += 1  # шаг цикла

        level = 0  # количество пробелов перед def
        while level < len(data[i]) and data[i][level] == ' ':
            level += 1

        if (data[i].lstrip().startswith('def') or data[i].lstrip().startswith('async def'))\
                and data[i].endswith(':')\
                and i + 1 < len(data)\
                and data[i + 1].startswith(' ' * (level + 1)):
            # мы в функции!!!

            # создаём словарь[орегинал, на что заменяем(если None, то не заменяем)]
            l_v = {it: None for it in _arguments(data[i].lstrip(), have_annotations)}
            l_v['_'] = None

            func_begin = i
            i += 1
            while i < len(data) and data[i].startswith(' ' * (level + 1)):  # пока не вышли из функции
                assert data[i]

                for command in commands(data[i]):
                    # всё, что из глобальной области видимости запоменаем и не переименовываем
                    if command.startswith('global'):
                        variables = command[7:].split(',')
                        for it in variables:  # итерируемся по переменным из глобальной облости видимости
                            assert reg_var.match(it) and it not in l_v.keys()
                            l_v[it] = None  # обозначаем, что заменять не надо
                    else:
                        if have_annotations:
                            t = [command]
                            delete_annotations(t)
                            command = t[0]

                        if not reg_make_vars.match(command):
                            continue

                        # проходим сюда когда действие command создаёт переменные
                        variables = command[:command.find('=')].split(',')
                        for it in variables:
                            if it[0] == '*':
                                it = it[1:]
                            assert '*' not in it

                            if it not in l_v.keys():
                                l_v[it] = f'_{_convert_base(abs(hash(it)))}'  # генерируем новое имя

                i += 1  # шаг цикла. идём по всей функции

            func_end = i - 1  # i это уже следующая после конца функции строка

            while i > func_begin:
                i -= 1  # шаг цикла. идём назад к началу функции

                # проверяем на каждой строчке наличае переменных, которые заменяются
                for it in filter(partial(getitem, l_v), l_v.keys()):  # итерируемся по тем, что не None
                    while True:
                        match = search(it, data[i])
                        if not match:
                            break

                        # заменяем совпвыший фрагмент
                        data[i] = data[i][:match.start()] + l_v[it] + data[i][match.end():]

            i = func_end  # далее будем искать функции уже после рассмотренной
