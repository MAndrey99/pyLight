import postprocessing


def test_del_asserts():
    case1 = {
        "from time import go;to go export time;": None,
        "assert PASS": "pass",
        "for i in range(asserto):assert a > (b if a else a.f())": "for i in range(asserto):pass",
        "def f():if a == b:assert c;TODO()": "def f():if a == b:pass;TODO()",
        "a+=1;assert a<=v^c;a-=c": "a+=1;pass;a-=c",
        "a='assert foo'": None,
        "a='assert foo'+'assert bar';assert baz": "a='assert foo'+'assert bar';pass",
        "  assert True is False, not got;a+=1;assert PASS;pass": "  pass;a+=1;pass;pass"
    }

    a, b = list(case1.keys()), list(case1.values())
    postprocessing.del_asserts(a)

    for i, j in zip(a, b):
        assert j is None or i == j
