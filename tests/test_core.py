import core
import re


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
        ("\n\t\t\n\n\t\ta,b\n\n\n", ['  a,b']),
        ("  '''\n\n # heh'''\n\n  # comment \n  text\n\n  r\"\"\"  # heh\"\"\"", ['  text']),
        ("'# \\'#\\' #'", ["'# \\'#\\' #'"]),
        ("'# ' + '#\\\\' #", ["'# ' + '#\\\\'"]),
        (r'a"\n\n"b', [r'a"\n\n"b']),
        (" xaxaxa = '#' # FFF", [" xaxaxa = '#'"]),
        ("\n  \nxaxaxa    # comment", ["xaxaxa"]),
        ("t = r'''\n xe # c\n\n'''", ["t = r'''", " xe # c", "", "'''"]),
        ("'''fgyuik/\\ed'''\na", ['a']),
        ("fr'''xe'''\n" + 'rb"""xe"""', []),
        ("sdfr\n'''sdfr7890(*&/* ss\t({'''", ["sdfr"]),
        ("ss\\n'''s'''", ["ss\\n'''s'''"]),
        ("r'''ooo ye'''\nxaxa\nr'''xxx'''\n", ["xaxa"]),
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
        (["from  logging import ERROR, INFO"], ["from logging import ERROR,INFO"]),
        (["if __name__ == __main__: "], ["if __name__==__main__:"]),
        (["    hello = ' hello  \\\\' + 'a'", "   t  +=1 "], ["    hello=' hello  \\\\'+'a'", "   t+=1"]),
        (['a = f"hello, { name + t }"'], ['a=f"hello, {name+t}"']),
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
        (["D = {'b': '\\<bs>',", "     's\\\\': ' '}"], ["D = {'b': '\\<bs>','s\\\\': ' '}"]),
        (["for i in a:", "  r(a)", "  p(i)", "kek"], ["for i in a:", "  r(a);p(i)", "kek"]),
        (["a = [", "   a,", "   b", "  ]"], ["a = [a,b]"]),
        (
            ["for c in (b' !',", "b'?@',", "b'\t'):", "  _[c] = chr(c)"],
            ["for c in (b' !',b'?@',b'\t'):_[c] = chr(c)"]
        ),
        (
            ["from sys import argv", "from logging import ERROR, INFO", "LOCATION = Path(argv[0]).parent"],
            ["from sys import argv;from logging import ERROR, INFO;LOCATION = Path(argv[0]).parent"]
        ),
        (
            ["if (e == 'dot' or", "e=='cfws' and", "e=='dot'):", "  append(Defect(", "'\na += b\nc\n'))"],
            ["if (e == 'dot' or e=='cfws' and e=='dot'):append(Defect('\na += b\nc\n'))"]
        ),
        (
            ['import re_and', 'from typing import List, Iterator', 'from operator import getitem',
             'from functools import partial', 'from io import StringIO', 'from core import _generate_mask'],
            ['import re_and;from typing import List, Iterator;from operator import getitem;'
             'from functools import partial;from io import StringIO;from core import _generate_mask']
        )
    ]

    for i, j in cases:
        core.optimize_str_count(i)
        assert i == j


def test_update_multiline_strings():
    cases = [
        (["a = '''", "b\\", "c '''"], ["a = '\\nbc '"]),
        (["kek", "a = '''", "", "", "rt'''", "lol"], ['kek', "a = '\\n\\n\\nrt'", 'lol']),
        ([" x x x ", 't = \'"""\'', "yur", 'a'], [' x x x ', 't = \'"""\'', 'yur', 'a']),
        ([" x ", ' p = """', "r e d_ ", 'rt"""', ' x'], [' x ', " p = '\\nr e d_ \\nrt'", ' x']),
        ([""" х='\\'\\'\\''""", """s=\"\"\"''''\"\"\"""", "xe"], [" х='\\'\\'\\''", 's="""\'\'\'\'"""', 'xe']),
        (["\"'\\\"\\\"\\\"'\"", "\"'\\\"\\\"\\\"'''\"", '"\\""'], ['"\'\\"\\"\\"\'"', '"\'\\"\\"\\"\'\'\'"', '"\\""']),
        (["'\\\\' + 'xa'", "oops"], ["'\\\\' + 'xa'", 'oops']),
        (["r = f'''", "", "xex", "'''", "foo = bar = '''baz'''"], ["r = '\\n\\nxex\\n'", "foo = bar = '''baz'''"]),
        (['r = """', '_ """ + \'\'\'', "a b c", "", "'''"], ["r = '\\n\\n_ ' + '\\na b c\\n\\n'"],),
        (['t = r"""', '', '\\ten"""'], ["t = '\\n\\n\\\\ten'"]),
        (['t = rb"""', '"text"', 'a""".replace(a, "xe")'], ['t = b\'\\n"text"\\na\'.replace(a, "xe")']),
        (["t = f'''", "text{value:.2f}text2", "xa", "'''[1:]"], ["t = '\\ntext{:.2f}text2\\nxa\\n'.format(value)[1:]"]),
        (["t = rf'''\\n", "{a if a else b}", "'''"], ["t = '\\\\n\\n{}\\n'.format(a if a else b)"]),
        (["t = r'''\\", "text\\", "end'''"], ["t = '\\\\\\ntext\\\\\\nend'"]),
    ]

    for i, j in cases:
        core.update_multiline_strings(i)
        assert i == j


def test_generate_mask():
    # проверяем саму маску
    cases = [
        ("h e l l o# 'rrr", to_bool_array('0'*9)),
        ("a = b'yt \" w\"' + 's'", to_bool_array('(0*6)(1*7)(0*5)10')),
        ("a = f'yt {oops} \" w\"'", to_bool_array('(0*6)(1*4)(0*4)(1*6)0')),
        ("a = f'yt {a + ba if \"xe}\" in {1, 2, 3} else ooo}'", to_bool_array('(0*6)(1*4)(0*11)111(0*23)10')),
        ("r''' \\'\\'\\' end'''", to_bool_array('000011111111111000')),
        (r"a = '\n'+'''b\\'''+'\n'+'''c '''", to_bool_array('(0*5)11(0*5)111(0*5)11(0*5)11000')),
        ('t = b\'\\n\'+rb"""text"""+b\'\\n\'+rb"""a"""', to_bool_array('(0*6)11(0*7)1111(0*6)11(0*7)1000')),
        (
            't =f"{no in \'\'\'text\'\'\'} and {\'\'\'t=\'t\' \'\'\' in no}"',
            to_bool_array('(0*5)1(0*9)1111000(1*7)000(1*6)(0*9)10')
        )
    ]

    for i, j in cases:
        i, s = core._generate_mask(i)
        assert len(i) == len(j)
        assert not s
        assert i == j

    # проверяем способность опознавать незакрытые строки
    cases = [
        ("a = rb'''", "rb'''"),
        ("a = br'''", "rb'''"),
        ("a = fr'''", "rf'''"),
        ("'tooo", "'"),
        ('r""" \'\'\' """ + """', '"""'),
        ('  r"""  ', 'r"""')
    ]

    for i, j in cases:
        _, i = core._generate_mask(i)
        assert i == j

    # проверяем способность опознавать незакрытые строки с учётом того, что сторока в многострочной строке
    cases = [
        ("xe", '"""', '"""'),
        ("to ''' tooo ''' toooooo''t'", "'''", "'''"),
        ("'rr'''r'", "'''", "r'"),
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


def test_minimize_left_space():
    data_in = [
        "hello!",
        "   my name is Andrey!",
        "     I am a student of electrotechnical University!",
        " this is a simple test..."
    ]

    data_out = [
        "hello!",
        "  my name is Andrey!",
        "   I am a student of electrotechnical University!",
        " this is a simple test..."
    ]

    core.minimize_left_space(data_in)
    assert data_in == data_out
