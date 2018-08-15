from pathlib import Path
from os import system
from sys import platform, argv
from time import perf_counter

import core
import postprocessing

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
     _   _
__ _/ | / |
\ V / |_| |
 \_/|_(_)_|
"""

HELP = """
ключевые параметры:  
'--enable_annotations'  - не удалять анотации функций
--noasserts или -a  -  все assert'ы будут удалены из кода.
--rename    или -r  - все имена локальных переменных будут изменены.
--nonewdir  или -d  - все изменённые файлы/директории записываются взамен старых.
--help      или -h  - получить справочную информацию
"""


# Настройки
no_asserts = False
rename_locals = False
no_new_dir = False
enable_annotations = False
show_time = False


def process(data: str) -> str:
    # получили не пустые строки без комментариев
    data = core.super_split(data)

    # многострочные строки в одну линию
    core.update_multiline_strings(data)

    # уменьшаем число отступов где это возможно
    core.minimize_left_space(data)

    # соеденяем строки если это возможно
    core.optimize_str_count(data)

    # удаляем пробелы между операторами
    core.del_spaces(data)

    # удаляем анотации функций
    if not enable_annotations:
        postprocessing.delete_annotations(data)

    # удаляем assert'ы
    if no_asserts:
        postprocessing.del_asserts(data)

    # пререименовываем локальные переменные
    if rename_locals:
        postprocessing.rename_locals(data, enable_annotations)

    return '\n'.join(data)


def process_path(p: Path):
    def for_each_in_dir(r_folder: Path, w_folder: Path, add: str=''):
        """
        обрабатывает все файлы в указанной дирректории

        :param r_folder: папка в которой лежат исходные файлы
        :param w_folder: папка в которую пишутся обработанные файлы
        """
        for it in r_folder.iterdir():
            if it.is_dir() and it.stem[0] != '.':
                if it.name == "Light":
                    continue

                new_w_folder = w_folder

                if w_folder:
                    new_w_folder = w_folder / it.name
                    if not new_w_folder.is_dir():
                        new_w_folder.mkdir()  # создаём подпапку для результата

                for_each_in_dir(it, new_w_folder, add + it.name + '/')
            elif it.is_file() and it.suffix in ('.py', '.pyw'):
                print("обработка", add + it.name)
                (w_folder / it.name if w_folder else it).write_text(
                                                                        process(it.read_text(encoding="utf-8-sig")),
                                                                        encoding="utf-8-sig"
                                                                   )

    # создаём папку для результатоа работы программы
    result_dir = None if no_new_dir else Path((p.parent if p.is_file() else p) / "Light")
    if result_dir and not result_dir.is_dir():
        result_dir.mkdir()  # создаём папку для результата

    t = perf_counter()  # сохраняем время начала процедуры для подсчёта быстродействия

    if p.is_file():
        (result_dir / p.name if result_dir else p).write_text(
                                                                process(p.read_text(encoding="utf-8-sig")),
                                                                encoding="utf-8-sig"
                                                             )
    else:
        for_each_in_dir(p, result_dir)

    if show_time:
        print(round((perf_counter() - t) * 1000), 'ms')


def menu():
    global no_asserts, rename_locals, no_new_dir

    print(HEAD, VERSION, '\n')

    # выводим настройки
    print("удаление assert'ов(1) -", no_asserts)
    print("переименовывание локальных переменных(2) -", rename_locals)
    print("создание новой директории для результата(3) -", not no_new_dir)

    print("\nВведите путь до нужного файла/папки или номер настройки, которую хотите изменить.\n"
          "'exit' - завершение программы.")

    # обработка ввода
    while True:
        text = input('> ')
        if text.isdigit() and 1 <= int(text) <= 3:
            text = int(text)
            if text == 1:
                no_asserts = not no_asserts
            elif text == 2:
                rename_locals = not rename_locals
            elif text == 3:
                no_new_dir = not no_new_dir

            system('cls' if platform == 'win32' else 'clear')
            menu()
            return

        if text == 'exit':
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
        print()


def main():
    global no_asserts, rename_locals, no_new_dir, enable_annotations

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
                    no_asserts = True
                elif i[2:] == 'renameVars':
                    rename_locals = True
                elif i[2:] == 'nonewdir':
                    rename_locals = True
                elif i[2:] == 'enable_annotations':
                    enable_annotations = True
            else:
                assert len(i) >= 2
                i = i[1:]

                while i:
                    if i[0] == 'a':
                        no_asserts = True
                    elif i[0] == 'r':
                        rename_locals = True
                    elif i[0] == 'd':
                        no_new_dir = True
                    else:
                        print(f"Передан неверный ключ!({i[0]})")
                        return

                    i = i[1:]
        else:
            i = Path(i)

            if not i.exists():
                print(f"Ошибка! Путь {i} не существует!")
                return

            assert i.is_dir() or i.is_file()
            targets.append(i)

    # обробатываем все питоновские скрипты по переданным путям
    for i in targets:
        assert (i.is_file() and i.suffix in ('.py', '.pyw')) or i.is_dir()
        process_path(i)


if __name__ == "__main__":
    main()
