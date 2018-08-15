import re
from random import randint

import postprocessing


def test_del_asserts():
    case1 = {
        "from time import go;to go export time;": "from time import go;to go export time;",
        "assert PASS": "pass",
        "for i in range(asserto):assert a > (b if a else a.f())": "for i in range(asserto):pass",
        "def f():if a == b:assert c;TODO()": "def f():if a == b:TODO()",
        "a+=1;assert a<=v^c;a-=c": "a+=1;a-=c",
        "a='assert foo'": "a='assert foo'",
        "a='assert foo'+'assert bar'": "a='assert foo'+'assert bar'",
        "  assert True is False, not got;a+=1;pass": "  a+=1;pass",
        "i,s=core._generate_mask(i);assert not s;assert False": "i,s=core._generate_mask(i)"
    }

    a, b = list(case1.keys()), list(case1.values())
    postprocessing.del_asserts(a)

    for i, j in zip(a, b):
        assert i == j


def test_delete_annotations():
    data_in = [
        "from postprocessing import delete annotations as da",
        "if a>b:a,b=b,a",
        "else:c:List[Dicrt[int,Tuple[str]]]=5",
        "da:Dict[function, int]",
        "da:function.magic._Da_",
        "da+=1",
        "da=15;da+=1",
        "____:Magic if da else not Magic=1771717175**16.f('gg')",
        "async def my_super_f(xe)->int:pass",
        "async def my_super_f(xe:Sum_type=15,n:int.___,*r,ppp:int=',t:OPEN[in):',p=True,op:List[int],**):pr(',k):')",
        "async def my_super_f(xe:Sum_type=15,n:int._,*,ppp:int=',**t:OPEN',p=True,op:Dict[int,List[float]]={1:[.5]}):",
        "def my_super_f(xe:Sum_type=15,n:int._,*,ppp:int=',**t:OPEN',p=True,op:Dict[int,List[float]]={1:[.5]}):",
        "def f(data:str)->List[str]:",
        "try:print(';hello:bebebe=xm;')",
        "finally:print(a+'=')",
        "a:PyLight=5;b:PyLight=5",
    ]

    data_out = [
        "from postprocessing import delete annotations as da",
        "if a>b:a,b=b,a",
        "else:c=5",
        "da+=1",
        "da=15;da+=1",
        "____=1771717175**16.f('gg')",
        "async def my_super_f(xe):pass",
        "async def my_super_f(xe=15,n,*r,ppp=',t:OPEN[in):',p=True,op,**):pr(',k):')",
        "async def my_super_f(xe=15,n,*,ppp=',**t:OPEN',p=True,op={1:[.5]}):",
        "def my_super_f(xe=15,n,*,ppp=',**t:OPEN',p=True,op={1:[.5]}):",
        "def f(data):",
        "try:print(';hello:bebebe=xm;')",
        "finally:print(a+'=')",
        "a=5;b=5",
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
            ' def super_func(yey:bool,*,xex=SUPER_TRUE,**kwargs)->xex:',
            '     t=yey-xex',
            '     print(f"{string[:t.sum_method()]} xexexe")',
            '     async def megafunc(xex=yey,moo:List[int]=t):',
            '         if SUPER_TRUE:xex:int=yey',
            '         else:t:str=5',
            '         y,*_,xex=yey+";moo=k";moo:List[int]=t+k',
            '     k:int=megafunc',
            ' def f2():',
            '     global SUPER_TRUE',
            '     false=False',
            '     SUPER_TRUE=false',
            '     return SUPER_TRUE or false'
        ], [
            ' SUPER_TRUE,T=True,Temp',
            ' def super_func(yey:bool,*,xex=SUPER_TRUE,**kwargs)->xex:',
            '     <hash0>=yey-xex',
            '     print(f"{string[:<hash0>.sum_method()]} xexexe")',
            '     async def megafunc(xex=yey,<hash1>:List[int]=<hash0>):',
            '         if SUPER_TRUE:xex:int=yey',
            '         else:<hash0>:str=5',
            '         <hash4>,*_,xex=yey+";moo=k";<hash1>:List[int]=<hash0>+<hash2>',
            '     <hash2>:int=megafunc',
            ' def f2():',
            '     global SUPER_TRUE',
            '     <hash3>=False',
            '     SUPER_TRUE=<hash3>',
            '     return SUPER_TRUE or <hash3>'
        ])
    postprocessing.rename_locals(case[0])

    # так как при каждом запуске питона хэши разные неоьзя просто сравнивать строки
    reg = re.compile(r'<hash(?P<number>\d)>')
    hashes = dict()  # здесь храним хэши. номер(симвал) - значение

    for a, b in zip(*case):
        while True:
            match = reg.search(b)  # ищем где должен быть хэш

            if not match:
                break

            if match.group('number') not in hashes.keys():  # если хэш с этим номером видим в первый раз
                t = ''  # хэшь, на этом
                i = match.start()

                while i < len(a) and a[i] in "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZqwertyuiopasdfghjklzxcvbnm_":
                    t += a[i]
                    i += 1

                assert t[0] == '_'
                hashes[match.group('number')] = t

            # заменяем <hash> на настоящий хэш
            b = b[:match.start()] + hashes[match.group('number')] + b[match.end():]

        assert a == b


def test_convert_base():
    for i in range(100):
        n = randint(0, 10**10)
        base = randint(2, 32)

        assert int(postprocessing._convert_base(n, base), base) == n


def test_fragment():
    string = 'my super mega long string!!!'

    for i in range(len(string) // 2):
        # фрагмент с левого краю
        fr = postprocessing.Fragment(string, 0 if i % 2 == 0 else None, i)
        assert str(fr) == string[:i] == fr.value
        fr.value += 'xe'
        assert fr.value == string[:i] + 'xe'
        assert fr.update(string) == string[:i] + 'xe' + string[i:]
        del fr.value
        assert fr.update(string) == string[i:]

        # фрагмент с правого краю
        fr = postprocessing.Fragment(string, i, len(string) if i % 3 == 0 else None)
        assert str(fr) == string[i:] == fr.value
        fr.value += 'xe'
        assert fr.value == string[i:] + 'xe'
        assert fr.update(string) == string + 'xe'
        del fr.value
        assert fr.update(string) == string[:i]

        # пустой фрагмент
        fr = postprocessing.Fragment(string, i, i)
        assert str(fr) == '' == fr.value
        assert fr.update(string) == string
        fr.value += 'xe'
        assert fr.value == 'xe'
        assert fr.update(string) == string[:i] + 'xe' + string[i:]
        del fr.value
        assert fr.update(string) == string

        # случайный фрагмент
        if len(string) - i > 3:
            end = randint(i, len(string))

            fr = postprocessing.Fragment(string, i, end)
            assert str(fr) == string[i:end] == fr.value
            fr.value += 'xe'
            fr.value = fr.value.upper()
            assert fr.value == string[i: end].upper() + 'XE'
            assert fr.update(string) == string[:i] + string[i: end].upper() + 'XE' + string[end:]
            del fr.value
            assert fr.update(string) == (string[:i] + string[end:])
