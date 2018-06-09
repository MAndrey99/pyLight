import core


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


def menu():
    pass  # TODO


def main():
    from sys import argv
    from pathlib import Path

    assert len(argv) > 1
    targets = [Path(i) for i in argv[1:]]

    for i in targets:
        assert (i.is_file() and i.suffix in ('.py', '.pyw')) or i.is_dir()

        if i.is_file():
            i.write_text(process(i.read_text(encoding="utf8")))
        else:
            def for_each_in_dir(dir: Path):
                for it in dir.iterdir():
                    if it.is_dir():
                        for_each_in_dir(it)
                    elif it.is_file() and it.suffix in ('.py', '.pyw'):
                        print("обработка", it.name)
                        it.write_text(process(it.read_text(encoding="utf8")))
            for_each_in_dir(i)


if __name__ == "__main__":
    main()
