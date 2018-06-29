from pathlib import Path
from os import system
from sys import platform, argv
import core

HEAD = r"""
             _      _       _     _
            | |    (_)     | |   | |
 _ __  _   _| |     _  __ _| |__ | |_
| '_ \| | | | |    | |/ _` | '_ \| __|
| |_) | |_| | |____| | (_| | | | | |_
| .__/ \__, |______|_|\__, |_| |_|\__|
| |     __/ |          __/ |
|_|    |___/          |___/"""

VERSION = r"""
     _   __
__ _/ | /  \
\ V / || () |
 \_/|_(_)__/
 """

HELP = """
ключевые параметры:  
--noasserts или -a  -  все assert'ы будут удалены из кода.  
--rename    или -r  - все имена локальных переменных будут изменены.  
--nonewdir  или -d  - все изменённые файлы/директории записываются взамен старых.  
--help      или -h  - получить справочную информацию
"""


# Настройки
noasserts = False      # TODO: действие
rename_locals = False  # TODO: -||-
nonewdir = False


def process(data: str) -> str:
    # убираем многострочные комментарии
    data = core.del_multiline_comments(data)

    # получили не пустые строки без однострочных комментариев и комментариев в концах строк
    data = core.super_split(data)

    # многострочные строки в одну линию
    core.update_multiline_strings(data)

    # соеденяем строки если это возможно
    core.optimize_str_count(data)

    # удаляем пробелы между операторами
    core.del_spaces(data)

    return '\n'.join(data)


def process_path(p: Path):
    result_dir = None if nonewdir else Path(p / "Light")
    if result_dir and not result_dir.is_dir(): result_dir.mkdir()  # создаём папку для результата

    if p.is_file():
        (result_dir / p.name if result_dir else p).write_text(process(p.read_text(encoding="utf8")), encoding="utf8")
    else:
        def for_each_in_dir(dir: Path, result_dir: Path):
            for it in dir.iterdir():
                if it.is_dir():
                    if it.name == "Light":
                        continue

                    if result_dir:
                        result_dir /= it.name  # переходим в подпапку
                        if not result_dir.is_dir(): result_dir.mkdir()  # создаём подпапку для результата
                    for_each_in_dir(it, result_dir)
                elif it.is_file() and it.suffix in ('.py', '.pyw'):
                    print("обработка", it.name)
                    (result_dir / it.name if result_dir else it).write_text(process(it.read_text(encoding="utf8")), encoding="utf8")

        for_each_in_dir(p, result_dir)


def menu():
    global noasserts, rename_locals, nonewdir

    print(HEAD, VERSION, '\n')

    # выводим настройки
    print("удаление assert'ов(1) -", noasserts)
    print("переименовывание локальных переменных(2) -", rename_locals)
    print("создание новой директории для результата(3) -", not nonewdir)

    print()
    print("Введите путь до нужного файла/папки или номер настройки, которую хотите изменить.")

    while True:
        text = input('> ')
        if text.isdigit() and 1 <= int(text) <= 3:
            text = int(text)
            if text == 1:
                noasserts = not noasserts
            elif text == 2:
                rename_locals = not rename_locals
            elif text == 3:
                nonewdir = not nonewdir

            system("cls" if platform == 'win32' else 'clear')
            menu()
            return

        target = Path(text)

        if not target.exists():
            print("Ошибка! Неверный путь.")
            continue

        if not target.is_absolute():
            print("Ошибка! Путь должен быть абсолютным!\n")
            continue

        if (target.is_file() and target.suffix in ('.py', '.pyw')) or target.is_dir():
            process_path(target)
        else:
            print("Ошибка! Не верный путь.\n")


def main():
    global noasserts, rename_locals, nonewdir

    if len(argv) == 1:
        menu()  # Передаём власть менюшке
        return
    elif len(argv) == 2 and argv[1] in ('-h', '--help'):
        print(HELP)
        return

    #  парсим аргументы ручками
    targets = []
    for i in argv[1:]:
        if i.startswith('-'):
            if i.startswith('--'):
                if i[2:] == 'noasserts':
                    noasserts = True
                elif i[2:] == 'renameVars':
                    rename_locals = True
                elif i[2:] == 'nonewdir':
                    rename_locals = True
            else:
                assert len(i) >= 2
                if i[1] == 'a':
                    noasserts = True
                elif i[1] == 'r':
                    rename_locals = True
                elif i[1] == 'd':
                    nonewdir = True
        else:
            i = Path(i)

            if not i.exists():
                print(f"Ошибка! Путь {i} не существует!")
                return

            assert i.is_dir() or i.is_file()
            targets.append(i)

    for i in targets:
        assert (i.is_file() and i.suffix in ('.py', '.pyw')) or i.is_dir()
        process_path(i)


if __name__ == "__main__":
    main()
