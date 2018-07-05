from random import randint
import core
import re


# вернёт True один на count раз
def randbool(count: int = 2) -> bool:
    assert count > 1
    return not bool(randint(0, count - 1))


# превращает строку из 0 и 1 в булевский массив
def to_bool_array(string: str):
    # заменяем выражения в скобках
    while True:
        i = re.search(r'\((?P<value>\d+)\*(?P<count>\d+)\)', string)
        if not i: break
        string = string[:i.start()] + i.group('value')*int(i.group('count')) + string[i.end():]

    res = []
    i = 0
    while i < len(string):
        assert string[i] in '01'
        res.append(bool(int(string[i])))
        i += 1
    return res


def test_super_split():
    cases = [
        ("a\nb \n\tc\n", ['a', 'b', ' c']),
        ("\n\t\t\n\n\t\ta,b\\\n\n\n", ['  a,b']),
        ("  '''\n\n # heh'''\n\n  # comment \n  text\n\n  r\"\"\"  # heh\"\"\"", ['  text']),
        ("'# \\'#\\' #'", ["'# \\'#\\' #'"]),
        ("'# ' + '#\\\\' #", ["'# ' + '#\\\\'"]),
        (r'a"\n\n"b', [r'a"\n\n"b']),
        (" xaxaxa = '#' # FFF", [" xaxaxa = '#'"]),
        ("\n  \nxaxaxa    # comment", ["xaxaxa"]),
        ("t = r'''\n xe # c\n\n'''", ["t = r'''", " xe # c", "", "'''"]),

        ("'''fgyuik/\\ed'''\na", ['a']),
        ("sdfr\n'''sdfr7890(*&/* ss\t({'''", ["sdfr"]),
        ("ss\\n'''s'''", ["ss\\n'''s'''"]),
        ("r'''ooo ye'''\nxaxa\nr'''xxx'''\n", ["xaxa"]),
        ('if a or\\\n    b == 0: ...', ['if a or    b == 0: ...']),
        ('r"""oooo o"""\ntext:\n\n  r"""t\n\n"""\n  a = 5', ["text:", "  a = 5"]),
        ('a = """\nxe\n"""\nb = """\n"""', ['a = """', 'xe', '"""', 'b = """', '"""']),
        ('a # ee"\n\n\n', ['a'])
    ]

    for i, j in cases:
        assert core.super_split(i) == j


def test_del_spaces():
    cases = [
        ([" a + b - c / (kkks :15)  "], [" a+b-c/(kkks:15)"]),
        (["a:   r-v", "for i  in c"], ["a:r-v", "for i in c"]),
        (["from logging import ERROR, INFO"], ["from logging import ERROR,INFO"]),
        (["if __name__ == __main__: "], ["if __name__==__main__:"]),
        (["    hello = ' hello  \\\\' + 'a'", "   t  +=1 "], ["    hello=' hello  \\\\'+'a'", "   t+=1"]),
        (
            [" h = ' t  + ab t' + '''sde ' ddd'' dq '' e' '''", ' f = """ r +  v"rre  s""" + a'],
            [" h=' t  + ab t'+'''sde ' ddd'' dq '' e' '''", ' f=""" r +  v"rre  s"""+a']
        )
    ]

    for i, j in cases:
        core.del_spaces(i)
        assert i == j


def test_optimize_str_count():
    cases = [
        ([" a", "b", "   c"], [" a", "b", "   c"]),
        (["a", " b", " c"], ["a", " b;c"]),
        ([" for i:", "   a"], [" for i:a"]),
        (["class i:", " a", " b"], ["class i:", " a;b"]),
        (["a", "class B"], ["a", "class B"]),
        (["  a\\", "      b!"], ["  a b!"]),
        (["D = {'b': '\\<bs>',", "     's\\\\': ' '}"], ["D = {'b': '\\<bs>', 's\\\\': ' '}"]),
        (["for i in a:", "  r(a)", "  p(i)", "kek"], ["for i in a:", "  r(a);p(i)", "kek"]),
        (["a = [", "   a,", "   b", "  ]"], ["a = [a, b]"]),
        (
            ["for c in (b' !',", "b'?@',", "b'\t'):", "  _[c] = chr(c)"],
            ["for c in (b' !', b'?@', b'\t'):_[c] = chr(c)"]
        ),
        (
            ["from sys import argv", "from logging import ERROR, INFO", "LOCATION = Path(argv[0]).parent"],
            ["from sys import argv;from logging import ERROR, INFO;LOCATION = Path(argv[0]).parent"]
        ),
        (
            ["if (e == 'dot' or", "e=='cfws' and", "e=='dot'):", "  append(Defect(", "'\na += b\nc\n'))"],
            ["if (e == 'dot' or e=='cfws' and e=='dot'):append(Defect('\na += b\nc\n'))"]
        )
    ]

    for i, j in cases:
        core.optimize_str_count(i)
        assert i == j


def test_update_multiline_strings():
    cases = [
        (["a = '''", "b\\", "c '''"], [r"a = '\n'+'''b\\'''+'\n'+'''c '''"]),
        (["kek", "a = '''", "", "", "rt'''", "lol"], ["kek", "a = '\\n'+'\\n'+'\\n'+'''rt'''", 'lol']),
        ([" x x x ", 't = \'"""\'', "yur", 'a'], [" x x x ", 't = \'"""\'', "yur", 'a']),
        (
            [" x ", ' p = """', "r e d_ ", 'rt"""', ' x'],
            [" x ", r' p = ' + "'\\n'+" + '"""r e d_ """+' + "'\\n'+" + '"""rt"""', ' x']
        ),
        (
            [""" х='\\'\\'\\''""", """s=\"\"\"''''\"\"\"""", "xe"],
            [""" х='\\'\\'\\''""", """s=\"\"\"''''\"\"\"""", "xe"]
        ),
        (
            ["\"'\\\"\\\"\\\"'\"", "\"'\\\"\\\"\\\"'''\"", '"\\""'],
            ["\"'\\\"\\\"\\\"'\"", "\"'\\\"\\\"\\\"'''\"", '"\\""']
        ),
        (["'\\\\' + 'xa'", "oops"], ["'\\\\' + 'xa'", "oops"]),
        (
            ["r = '''", "", "xex", "'''", "foo = bar = '''baz'''"],
            ["r = '\\n'+'\\n'+'''xex'''+'\\n'+''''''", "foo = bar = '''baz'''"]
        ),
        (
            ['r = """', '_ """ + \'\'\'', "a b c", "", "'''"],
            ['r = \'\\n\'+"""_ """ + \'\\n\'+\'\'\'a b c\'\'\'+\'\\n\'+\'\\n\'+\'\'\'\'\'\''],
        )
    ]

    for i, j in cases:
        core.update_multiline_strings(i)
        assert i == j


def test_generate_mask():
    # проверяем саму маску
    cases = [
        ("h e l l o# 'rrr", to_bool_array('0'*9)),
        ("a = b'yt \" w\"' + 's'", to_bool_array('(0*6)(1*7)(0*5)10')),
        ("r''' \\'\\'\\' end'''", to_bool_array('000011111111111000'))
    ]

    for i, j in cases:
        i, s = core._generate_mask(i)
        assert len(i) == len(j)
        assert not s
        assert i == j

    # проверяем способность опознавать незакрытые строки
    cases = [
        ("a = b'''", "'''"),
        ("'tooo", "'"),
        ('r""" \'\'\' """ + """', '"""')
    ]

    for i, j in cases:
        _, i = core._generate_mask(i)
        assert i == j

    # проверяем способность опознавать незакрытые строки с учётом того, что сторока в многострочной строке
    cases = [
        ("xe", '"""', '"""'),
        ("to ''' tooo ''' toooooo''t'", "'''", "'''"),
        ("'rr'''r'", "'''", "'"),
        ('aass""", \'\'\'v', "'''", None)
    ]

    for i, j, k in cases:
        _, i = core._generate_mask(i, j)
        assert i == k

    # проверяем работу с учётом предыдущих строк
    cases = [
        ("xoo", None),
        ("xee '' t", None),
        ("t'r'a'x'i'", "'"),
        ("t'r'a'x'i'", None),
        ("a = '''", "'''"),
        ("t'r'a'x'i'", "'''"),
        ("None", "'''"),
        ("'''", None)
    ]

    for i, j in cases:
        _, i = core._generate_mask(i, 'last')
        assert i == j
