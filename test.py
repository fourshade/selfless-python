""" Basic functionality tests for selfless classes. """

import io
import sys
import timeit

from selfless import Selfless


class Writer(Selfless):

    # All instance vars must be declared in order to work inside the class.
    # Bare annotations such as '_strings: list' with no value do not work.
    # Anything assigned in __init__ can just default to None here.
    _strings = None
    _file = None
    delim = ''

    def __init__(file=None):
        """ Mutable objects such as lists must still be initialized
            in __init__ even if declared above. The string <delim>
            is immutable, so it can be left alone at the default. """
        _strings = []
        _file = file or sys.stdout

    def __len__():
        """ Special method test. """
        return len(_strings)

    def add(*args):
        """ Augmented assignment test. """
        _strings += args

    def set_delim(delim):
        """ Explicit self is still needed in the case of argument shadowing. """
        self.delim = delim

    def _write(s):
        _file.write(s)

    def write_all():
        """ Implicit and explicit self should work the same. """
        for s in _strings:
            self._write(delim)
            _write(s)


class WriterRight(Writer):

    _foo = 'RIGHT'  # gets shadowed

    def write_all():
        """ Super call goes to immediate parent. """
        _write('right')
        super.write_all()


class WriterLeft(Writer):

    _foo = 'LEFT'   # is exposed

    def write_all():
        """ Super call goes to *sibling* when combined in child class. """
        _write('left')
        super.write_all()


class WriterExtended(WriterLeft, WriterRight):

    _header = None  # New instance vars may be added in subclasses.

    def __init__(header, **kwargs):
        """ Super call with kwargs, skips 2 MRO levels. """
        super.__init__(**kwargs)
        _header = header

    def write_all(with_header=True):
        """ Test the full super call chain. """
        if with_header:
            _write(_header)
        _write(_foo)
        super.write_all()
        _write('END')


def test():
    buf = io.StringIO()
    x = WriterExtended('START', file=buf)
    x.add()
    x.add('1')
    x.add('2', '3')
    Writer.add(x, '4')
    string_count = len(x)
    x.add(f'L{string_count}')
    x.set_delim('/')
    x.write_all()
    return buf.getvalue()


def test_output():
    actual = test()
    expected = 'STARTLEFTleftright/1/2/3/4/L4END'
    print('Need: ' + expected)
    print('Got:  ' + actual)
    return int(actual != expected)


def test_bench(n, r=1):
    if r > 1:
        t = min(timeit.repeat(test, number=n//r, repeat=r)) * r
    else:
        t = timeit.timeit(test, number=n)
    print(f'Extrapolated best time for {n} runs: {t:.3f} seconds.')
    return 0


if __name__ == '__main__':
    args = sys.argv[1:]
    if args:
        code = test_bench(*map(int, args))
    else:
        code = test_output()
    sys.exit(code)
