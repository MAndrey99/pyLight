import re
from typing import List, Iterator
from operator import getitem
from functools import partial
from io import StringIO

from core import _generate_mask, _count_left_spaces


def del_asserts(data: List[str]):
    """
    заменяет все assert'ы на "pass" или удаляем их

    :param data: список обработанных строк кода
    """

    i = 0
    while i < len(data):
        mask, s = _generate_mask(data[i])
        assert not s  # все строки уже немногострочны
        assert '\n' not in data[i]

        # с помощью регулярки ищем assert'ы
        reg = re.compile(r"assert [^;]+")
        match = reg.search(data[i])

        # заменяем все, что находим на pass
        while match:
            if not mask[match.start()]:
                if match.start() > 0 and data[i][match.start() - 1] == ';':
                    data[i] = data[i][:match.start()-1] + data[i][match.end():]  # удаляем то что нашли и ';'
                    match = reg.search(data[i], pos=match.start())
                elif len(data[i]) > match.end() and data[i][match.end()] == ';':
                    data[i] = data[i][:match.start()] + data[i][match.end() + 1:]  # удаляем то что нашли и ';'
                    match = reg.search(data[i], pos=match.start())
                else:
                    data[i] = f'{data[i][:match.start()]}pass{data[i][match.end():]}'  # заменяем то что нашли на pass
                    match = reg.search(data[i], pos=match.start() + 4)

                    if data[i].lstrip() == 'pass':
                        del data[i]
                        i -= 1
                        break

                mask, s = _generate_mask(data[i])  # обновляем маску
                assert not s
            else:
                match = reg.search(data[i], pos=match.end())

        i += 1  # шаг цикла


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

        t = data[i].lstrip()
        if t.startswith('def ') or t.startswith('async def'):
            # удаляем аннотации функциии
            # ! данный метод не поддерживает функции и любые другие выражения

            mask, _ = _generate_mask(data[i])

            # удаляем аннотацию возвращаемого значения
            c = None  # позиция закрывающего список аргументов симвала

            for j in range(5, len(data[i])):
                if data[i][j] == ')' and not mask[j]:
                    c = j
                    break
            assert c

            c += 1
            dtots_p = c  # позиция двоеточия
            while data[i][dtots_p] != ':':
                dtots_p += 1

            data[i] = data[i][:c] + data[i][dtots_p:]  # вырезаем аннотацию возвращаемого значения

            # удаляем аннотации аргументов
            start = data[i].find('(') + 1

            # ищем конец функции
            t = len(data[i])
            while True:
                end = data[i][start: t].rfind('):') + start

                if not mask[end]:
                    break

                t = end - 2
            del t

            # в цикле находим и удаляем все анотации
            while True:
                match = reg_arg_annotation.search(data[i], pos=start, endpos=end)

                if not match:
                    break

                if not mask[match.start()]:  # если найденный фрагмент не в комментарии
                    data[i] = data[i][:match.start()] + data[i][match.end():]
                    mask = mask[:match.start()] + mask[match.end():]
                    end -= match.end() - match.start()

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
                        end -= p - match.start()
                else:
                    start = match.end()
        else:
            for it in _commands(data, i):
                mask, _ = _generate_mask(it.value)

                if reg_annotation.match(it.value):
                    def get_colon_pos() -> int:
                        """возвращает положения симвала ':' пред аннотацией или -1"""

                        n = 0  # номер просматриеваемого симвала
                        colon_pos = -1  # позиция симвала ':'

                        while n < len(it.value):
                            while it.value[n] != ':' and n < len(it.value):
                                n += 1

                            var_name = it.value[colon_pos + 1: n]
                            colon_pos = n

                            if var_name not in ['try', 'else', 'finally'] and reg_var.match(var_name):
                                break  # если вместо имени переменной ключевое слово, то здесь нет аннотации

                            if not reg_annotation.match(it.value[colon_pos + 1:]):
                                return -1

                            n += 1

                        return colon_pos

                    eq_pos = None
                    colon_pos = get_colon_pos()

                    if colon_pos != -1:
                        # ищем знак равно так чтобы не среагировать на операторы <=, !=, == и тд., а так же на строки
                        for j in range(colon_pos, len(mask)):
                            if not mask[j]:
                                if it.value[j] == '=' and it.value[j + 1] not in '<>!=' and it.value[j - 1] not in '<>!=':
                                    eq_pos = j
                                    break

                        # если эта строчка чисто аннотация, то её надо удалить!
                        if eq_pos is None:
                            del it.value
                            continue

                        it.value = it.value[:colon_pos] + it.value[eq_pos:]  # вырезаем саму аннотацию

        if data[i]:
            i += 1
        else:
            del data[i]


def _arguments(definition: str, have_annotations: bool) -> List[str]:
    """
    Даёт список аргументов обьявленной функции

    :param definition: строка с обьявлением функции без пробельных симвалов в начале
    """
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


class Fragment:
    __slots__ = ("_value", "_start", "_end")

    @property
    def value(self) -> str:
        return self._value

    @value.setter
    def value(self, value: str):
        self._value = value

    @value.deleter
    def value(self):
        self._value = ''

    def update(self, line: str) -> str:
        return (line[:self._start] if self._start is not None else '')\
               + self._value\
               + (line[self._end:] if self._end is not None else '')

    def __init__(self, line: str, _start: int=None, _end: int=None):
        self._value = line[_start: _end]
        self._start, self._end = _start, _end

    def __str__(self) -> str:
        return self._value


def _commands(data: List[str], index: int) -> Iterator[Fragment]:
    """разбиваем строку на выражения типа: a+=1;print(a) -> a+=1 и print(a)"""
    assert data[index].lstrip()

    begin = _count_left_spaces(data[index])  # начало рассматривоемого вырожения
    mask, _ = _generate_mask(data[index])

    i = begin
    while True:
        if data[index][i] == ';' and not mask[i]:
            fragment = Fragment(data[index], begin, i)
            yield fragment
            i += len(fragment.value) - fragment._end + fragment._start

            data[index] = fragment.update(data[index])
            begin = i + 1

        i += 1

        if i >= len(data[index]):
            break

    fragment = Fragment(data[index], begin)
    yield fragment
    data[index] = fragment.update(data[index])


def rename_locals(data: List[str], have_annotations=True):
    """
    переименовывает все локальные переменные в функциях

    :param have_annotations: возможно ли присудствие аннотаций функций в коде
    :param data: список обработанных строк кода
    """

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

        level = _count_left_spaces(data[i])  # количество пробелов перед def

        if (data[i][level:].startswith('def') or data[i][level:].startswith('async def'))\
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

                for command in _commands(data, i):
                    command = command.value  # нам не нужна тут изменять фрагменты строки data[i]

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
                it: str
                for it in filter(partial(getitem, l_v), l_v.keys()):  # итерируемся по тем, что не None
                    assert type(it) is str

                    while True:
                        match = search(it, data[i])
                        if not match:
                            break

                        # заменяем совпвыший фрагмент
                        data[i] = data[i][:match.start()] + l_v[it] + data[i][match.end():]

            i = func_end  # далее будем искать функции уже после рассмотренной
