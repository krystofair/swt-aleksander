"""
    Utils for processor units.
    First here are decorators for assign to task a type which object produce.
    unit, task is reference to the same, reference to function from processor module.
"""
import importlib
import logging
import re

from aleksander.models import AbstractObject

from attrs import define, field


log = logging.getLogger("processing")


@define
class PTask:
    regex = field(type=str)
    module = field(type=str)
    name = field(type=str)
    model = field(type=type[AbstractObject])

    @property
    def fqn(self):
        return '.'.join([self.module, self.name])

    @property
    def task(self):
        m = importlib.import_module(self.module)
        return getattr(m, self.name)

class ProcessorsReg:
    entries: list[PTask] = list()

    @classmethod
    def register(cls, pattern: str, model: type[AbstractObject]):
        def decorator(f):
            # part of registering
            try:
                if not pattern:
                    raise ValueError("Regex has to be defined.")
                if model is AbstractObject:
                    raise ValueError("Model has to be defined.")
                cls.entries.append(PTask(regex=pattern, module=f.__module__, name=f.__qualname__, model=model))
            except ValueError as e:
                log.warning("function {module}.{name} will not be found.")
                log.info(e)
            return f
        return decorator

    def __call__(self, *args, **kwargs):
        return self.__class__.register(*args, **kwargs)

    @classmethod
    def select(cls, url) -> PTask|None:
        """Returns procesor unit wrapper"""
        for entry in cls.entries:
            if re.search(entry.regex, url):
                return entry
        return None

#: this is object of registry for nice calling "register" method by __call__
#: otherwise it has to be in __init__ or something else.
reg = ProcessorsReg()

#: How to use it, example - rest is in test.py.
class TestObj(AbstractObject):
    pass
@reg(pattern='9532d4f0-077e-4e57-97f1-6022ced75124/.*$', model=TestObj)
def aaa(msg):
    return msg