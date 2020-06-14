""" HERE BE DRAGONS. That is all. """

import dis
OPS = type('opmap', (), dis.opmap)

_FN = lambda c: lambda: c
FunctionType = type(_FN)
CellType = type(_FN(0).__closure__[0])
del _FN


class BytecodeSubstitutions:

    def __init__(self, code):
        self._code = code
        self._sub_table = {}

    def _replace(self, **kwargs):
        self._code = self._code.replace(**kwargs)

    def _substitute(self):
        raw = bytearray(self._code.co_code)
        table = self._sub_table
        for i in range(0, len(raw), 2):
           inst = (raw[i], raw[i+1])
           if inst in table:
               raw[i:i+2] = table[inst]
        self._replace(co_code=bytes(raw))
        self._sub_table.clear()

    def _sub_free(self, from_names, to_names, ops):
        freevars = self._code.co_freevars
        new_free = set(to_names).difference(freevars)
        if new_free:
            freevars += tuple(new_free)
            self._replace(co_freevars=freevars)
        table = {}
        to_map = {name: i for i, name in enumerate(freevars)}
        for i, n in enumerate(from_names):
            if n in to_map:
                for oldop, newop in ops:
                    self._sub_table[oldop, i] = (newop, to_map[n])

    def global_to_deref(self, names):
        code = self._code
        global_refs = code.co_names
        self._sub_free(global_refs, names,
                       [(OPS.LOAD_GLOBAL,  OPS.LOAD_DEREF),
                        (OPS.STORE_GLOBAL, OPS.STORE_DEREF)])

    def local_to_deref(self, names, *, remove_args=True):
        code = self._code
        local_refs = list(code.co_varnames)
        if remove_args:
            nargs = code.co_argcount + code.co_kwonlyargcount
            flags = code.co_flags
            nargs += bool(flags & 0x08)  # VARARGS
            nargs += bool(flags & 0x10)  # VARKEYWORDS
            local_refs[:nargs] = [None] * nargs
        self._sub_free(local_refs, names,
                       [(OPS.LOAD_FAST,  OPS.LOAD_DEREF),
                        (OPS.STORE_FAST, OPS.STORE_DEREF)])

    def compile(self):
        self._substitute()
        return self._code


class CellMap:

    __slots__ = ('_d',)

    def __init__(self, cellvars=None, *, parent_map=None):
        self._d = {}
        if parent_map is not None:
            self._d.update(parent_map._d)
        if cellvars is not None:
            for k, v in cellvars.items():
                self._d[k] = CellType(v)

    def __getitem__(self, k):
        return self._d[k].cell_contents

    def __setitem__(self, k, v):
        self._d[k].cell_contents = v

    def make_closure(self, f):
        code = f.__code__
        subs = BytecodeSubstitutions(code)
        subs.global_to_deref(self._d)
        subs.local_to_deref(self._d)
        code = subs.compile()
        closure = f.__closure__ or ()
        extra_vars = code.co_freevars[len(closure):]
        closure += tuple([self._d[k] for k in extra_vars])
        new_f = FunctionType(code, f.__globals__, f.__name__,
                             f.__defaults__, closure)
        new_f.__kwdefaults__ = f.__kwdefaults__
        return new_f

    def close_all(self):
        for k in self._d:
            v = self[k]
            if type(v) is FunctionType:
                self[k] = self.make_closure(v)


class Descr:

    __slots__ = ('_k',)

    def __init__(self, k):
        self._k = k

    def call_unbound(self, inst, *args, **kwargs):
        func = self.__get__(inst, None)
        return func(*args, **kwargs)

    def __get__(self, inst, cls):
        if inst is None:
            return self.call_unbound
        return inst.cellmap[self._k]

    def __set__(self, inst, value):
        inst.cellmap[self._k] = value


class Super:

    def __init__(self, inst, cls, mro=None):
        if mro is None:
            mro = cls.__mro__[::-1]
        self._params = (inst, cls, mro)

    def __getattribute__(self, name):
        inst, cls, mro = super().__getattribute__('_params')
        mro = list(mro)
        f = last_f = mro[-1]._cellvars[name]
        while f is last_f:
            mro.pop()
            f = mro[-1]._cellvars[name]
        new_cellvars = {'super': Super(inst, cls, mro)}
        cellmap = CellMap(new_cellvars, parent_map=inst.cellmap)
        return cellmap.make_closure(f)


class Selfless:

    _cellvars = {}

    def __init_subclass__(cls):
        cellvars = cls._cellvars = {}
        for b in cls.__bases__:
            if not issubclass(b, Selfless):
                raise TypeError('Selfless classes cannot have self-ish bases.')
            cellvars.update(b._cellvars)
        base_vars = vars(Selfless)
        for k, v in vars(cls).items():
            if k not in base_vars:
                cellvars[k] = v
                setattr(cls, k, Descr(k))

    def __new__(cls, *args, **kwargs):
        self = object.__new__(cls)
        cellvars = {'self': self,
                    'super': Super(self, cls),
                    **cls._cellvars}
        self.cellmap = CellMap(cellvars)
        self.cellmap.close_all()
        return self
