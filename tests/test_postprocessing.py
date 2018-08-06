import postprocessing
import re


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
        "da:Dict[function, int]",
        "da:function.magic._Da_",
        "da+=1",
        "da=15",
        "____:Magic if da else not Magic=1771717175**16.f('gg')",
        "async def my_super_f(xe):pass",
        "async def my_super_f(xe:Sum_type=15,n:int.___,*r,ppp:int=',t:OPEN[in',p=True,op:List[int],**):pass",
        "async def my_super_f(xe:Sum_type=15,n:int._,*,ppp:int=',**t:OPEN',p=True,op:Dict[int,List[float]]={1:[.5]}):",
    ]

    data_out = [
        "from postprocessing import delete annotations as da",
        "da+=1",
        "da=15",
        "____=1771717175**16.f('gg')",
        "async def my_super_f(xe):pass",
        "async def my_super_f(xe=15,n,*r,ppp=',t:OPEN[in',p=True,op,**):pass",
        "async def my_super_f(xe=15,n,*,ppp=',**t:OPEN',p=True,op={1:[.5]}):",
    ]

    postprocessing.delete_annotations(data_in)
    assert data_in == data_out


def test_arguments():
    case1 = {
        "def ___f_____(a):": ['a'],
        "def f1o(a:int=5):": ['a'],
        "def _f1(a,b:bool,*p,c='yey:s,k',**):": ['a', 'b', 'p', 'c'],
        "async def _f1(a,b:List[int],*,c='yey:s,k',**kwargs):": ['a', 'b', 'c', 'kwargs']
    }

    for i in case1.keys():
        assert postprocessing._arguments(i, True) == case1[i]

    case2 = {
        "def ___f_____(a):": ['a'],
        "def f1o(a=5):": ['a'],
        "def _f1(a,b,*p,c='yey,k',**):": ['a', 'b', 'p', 'c'],
        "async def _f1(a,b,*,c='yey',**kwargs):": ['a', 'b', 'c', 'kwargs']
    }

    for i in case2.keys():
        assert postprocessing._arguments(i, False) == case2[i]


def test_rename_locals():
    case = \
([
    ' SUPER_TRUE,T=True,Temp',
    ' def super_func(yey:bool,*,xex=SUPER_TRUE,**kwargs):',
    '     t=yey-xex',
    '     async def megafunc(xex=yey,moo=t):',
    '         y,*_,xex=yey',
    '         moo=t+k',
    '     k=megafunc',
    ' def f2():',
    '     global SUPER_TRUE',
    '     false=False',
    '     SUPER_TRUE=false',
    '     return SUPER_TRUE or false'
], [
    ' SUPER_TRUE,T=True,Temp',
    ' def super_func(yey:bool,*,xex=SUPER_TRUE,**kwargs):',
    '     <hash0>=yey-xex',
    '     async def megafunc(xex=yey,<hash1>=<hash0>):',
    '         <hash4>,*_,xex=yey',
    '         <hash1>=<hash0>+<hash2>',
    '     <hash2>=megafunc',
    ' def f2():',
    '     global SUPER_TRUE',
    '     <hash3>=False',
    '     SUPER_TRUE=<hash3>',
    '     return SUPER_TRUE or <hash3>'
])
    postprocessing.rename_locals(case[0])

    # так как при каждом запуске питона хэши разные неоьзя просто сравнивать строки
    reg = re.compile(r'<hash(?P<number>\d)>')
    hashs = dict()  # здесь храним хэши. номер(симвал) - значение

    for a, b in zip(*case):
        while True:
            match = reg.search(b)  # ищем где должен быть хэш

            if not match:
                break

            if match.group('number') not in hashs.keys():  # если хэш с этим номером видим в первый раз
                t = ''  # хэшь, на этом
                i = match.start()

                while i < len(a) and a[i] in "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZqwertyuiopasdfghjklzxcvbnm_":
                    t += a[i]
                    i += 1

                assert t[0] == '_'
                hashs[match.group('number')] = t

            # заменяем <hash> на настоящий хэш
            b = b[:match.start()] + hashs[match.group('number')] + b[match.end():]

        assert a == b


def test_convert_base():
    from random import randint

    for i in range(100):
        n = randint(0, 10**10)
        base = randint(2, 32)

        assert int(postprocessing._convert_base(n, base), base) == n
