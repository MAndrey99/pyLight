import re
from typing import List

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
            if not any(mask[match.start(): match.end()]):
                data[i] = f'{data[i][:match.start()]}pass{data[i][match.end():]}'  # заменяем то что нашли на pass
                mask, s = _generate_mask(data[i])  # обновляем маску
                assert not s

                match = reg.search(data[i])
            else:
                match = reg.search(data[i], pos=match.end())


def rename_locals(data: List[str]):
    raise Exception  # TODO
