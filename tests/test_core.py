from random import randint, choice
import core


# вернёт True один на count раз
def randbool(count: int = 2) -> bool:
    assert count > 1
    return not bool(randint(0, count - 1))


def test_del_multiline_comments():
    cases = [
        ("'''fgyuik/\\ed'''\na", 'a'),
        ("sdfr\n'''sdfr7890(*&/* ss\t({'''", "sdfr"),
        ("ss\\n'''s'''", "ss\\n'''s'''"),
        ("r'''ooo ye'''\nxaxa\nr'''xxx'''\n", "xaxa\n"),
        ('r"""oooo o"""\ntext:\n\n  r"""t\n\n"""\n  a = 5', "text:\n  a = 5")
    ]

    for i, j in cases:
        assert core.del_multiline_comments(i) == j
    del cases

    def rand_text(min_l: int, max_l: int) -> str:
        res = ''
        for _ in range(randint(min_l, max_l)):
            res += chr(randint(ord('a'), ord('z'))) if randbool() else choice('!@#$%^&*()_+=1234567890/.?\n*->}')
        return res

    for i in range(250):
        t = choice(('"""', "'''"))
        res = ''
        s = ''
        
        # добавляем комментарий в начало
        if randbool(5): s += t + rand_text(0, 100) + t + '\n'
        
        for _ in range(randint(0, 100)):
            # добавляем текст
            if not randbool(10):
                text = rand_text(0, 50) + '\n'
                s += text
                res += text
            
            # добавляем комментарий
            if randbool():
                s += t + rand_text(0, 100) + t + '\n'

        # print("s:\n", s, '\n---------------------------------------------------------------')
        s = core.del_multiline_comments(s)
        while s and s[-1] == '\n': s = s[:-1]
        while res and res[-1] == '\n': res = res[:-1]
        while s and s[0] == '\n': s = s[1:]
        while res and res[0] == '\n': res = res[1:]
        while '\n\n' in s: s = s.replace('\n\n', '\n')
        while '\n\n' in res: res = res.replace('\n\n', '\n')

        assert s == res


def test_super_split():
    cases = [
        ("a\nb \n\tc\n", ['a', 'b', ' c']),
        ("\n\t\t\n\n\t\ta,b\\\n\n\n", ['  a,b\\']),
        ("''' # heh'''\nr\"\"\" # heh\"\"\"", ["''' # heh'''", 'r""" # heh"""']),
        ("'# \\'#\\' #'", ["'# \\'#\\' #'"]),
        ("'# ' + '#\\\\' #", ["'# ' + '#\\\\'"]),
        (r'a"\n"b', [r'a"\n"b']),
        (" xaxaxa = '#' # FFF", [" xaxaxa = '#'"]),
        ("\n  \nxaxaxa    # comment", ["xaxaxa"])
    ]

    for i, j in cases:
        assert core.super_split(i) == j


def test_del_spaces():
    cases = [
        ([" a + b - c / (kkks :15)  "], [" a+b-c/(kkks:15)"]),
        (["a:   r-v", "for i  in c"], ["a:r-v", "for i in c"]),
        (["from logging import ERROR, INFO"], ["from logging import ERROR,INFO"]),
        (["if __name__ == __main__: "], ["if __name__==__main__:"]),
        (["    hello = ' hello  '", "   t  +=1 "], ["    hello=' hello  '", "   t+=1"]),
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
        (["D = {'b': '\\<bs>',", "     's': ' '}"], ["D = {'b': '\\<bs>', 's': ' '}"]),
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
        (["a = '''", "b", "c '''"], [r"a = '\n'+'''b'''+'\n'+'''c '''"]),
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
        (["'\\\\' + 'xa'", "oops"], ["'\\\\' + 'xa'", "oops"])
    ]

    for i, j in cases:
        core.update_multiline_strings(i)
        assert i == j
