import postprocessing
from pathlib import Path


def test_del_asserts():
    case1 = {
        "from time import go;to go export time;": None,
        "assert PASS": "pass",
        "for i in range(asserto):assert a > (b if a else a.f())": "for i in range(asserto):pass",
        "def f():if a == b:assert c;TODO()": "def f():if a == b:pass;TODO()",
        "a+=1;assert a<=v^c;a-=c": "a+=1;pass;a-=c",
        "a='assert foo'": None,
        "a='assert foo'+'assert bar';assert baz": "a='assert foo'+'assert bar';pass",
        "  assert True is False, not got;a+=1;assert 'p' in PASS;pass": "  pass;a+=1;pass;pass"
    }

    a, b = list(case1.keys()), list(case1.values())
    postprocessing.del_asserts(a)

    for i, j in zip(a, b):
        assert j is None or i == j


def test_delete_annotations():
    data_in = [
        "from postprocessing import delete annotations as da",
        "da:function",
        "da:function.magic._Da_",
        "da+=1",
        "da=15",
        "____:Magic if da else not Magic=1771717175**16.f('gg')",
        "async def my_super_f(xe):pass",
        "async def my_super_f(xe:Sum_type=15,n:int.___,*r,ppp:int=',t:OPEN',p=True):pass",
    ]

    data_out = [
        "from postprocessing import delete annotations as da",
        "da+=1",
        "da=15",
        "____=1771717175**16.f('gg')",
        "async def my_super_f(xe):pass",
        "async def my_super_f(xe=15,n,*r,ppp=',t:OPEN',p=True):pass",
    ]

    # TODO: проверка удаления в функциях

    postprocessing.delete_annotations(data_in)
    assert data_in == data_out


def test_rename_locals():
    test_data = Path('rename_locals_tests.py').read_text().split('\n')
    postprocessing.rename_locals(test_data)
    print('\n'.join(test_data))
    # TODO


def test_convert_base():
    from random import randint

    for i in range(100):
        n = randint(0, 10**10)
        base = randint(2, 32)

        assert int(postprocessing._convert_base(n, base), base) == n

