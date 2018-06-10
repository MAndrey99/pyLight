from pathlib import Path
import core

HEAD = """
             _      _       _     _
            | |    (_)     | |   | |
 _ __  _   _| |     _  __ _| |__ | |_
| '_ \| | | | |    | |/ _` | '_ \| __|
| |_) | |_| | |____| | (_| | | | | |_
| .__/ \__, |______|_|\__, |_| |_|\__|
| |     __/ |          __/ |
|_|    |___/          |___/"""

VERSION = """
      __   ___
__ __/  \ |_  )
\ V / () | / /
 \_/ \__(_)___|
 """


def process(data: str) -> str:
    # убираем многострочные комментарии
    data = core.del_multiline_comments(data)

    # получили не пустые строки без однострочных комментариев и комментариев в концах строк
    data = core.super_split(data)

    # соеденяем строки
    core.optimize_str_count(data)

    # удаляем пробелы между операторами
    core.del_spaces(data)

    return '\n'.join(data)


def process_path(p: Path):
    if p.is_file():
        p.write_text(process(p.read_text(encoding="utf8")))
    else:
        def for_each_in_dir(dir: Path):
            for it in dir.iterdir():
                if it.is_dir():
                    for_each_in_dir(it)
                elif it.is_file() and it.suffix in ('.py', '.pyw'):
                    print("обработка", it.name)
                    it.write_text(process(it.read_text(encoding="utf8")))

        for_each_in_dir(p)


def menu():
    print(HEAD, VERSION, '\n')
    print("Введите путь до нужного файла/папки")

    while True:
        target = Path(input('> '))

        if not target.is_absolute():
            print("Ошибка! Путь должен быть абсолютным!\n")
            continue

        if (target.is_file() and target.suffix in ('.py', '.pyw')) or target.is_dir():
            process_path(target)
        else:
            print("Ошибка! Не верный путь.\n")


def main():
    from sys import argv

    if len(argv) == 1:
        menu()  # Передаём власть менюшке
        return

    targets = [Path(i) for i in argv[1:]]

    for i in targets:
        assert (i.is_file() and i.suffix in ('.py', '.pyw')) or i.is_dir()
        process_path(i)


if __name__ == "__main__":
    main()
