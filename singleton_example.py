from copy import deepcopy
from contexting_lib.decorators import default, thread_bound
from contexting_lib.runtime_context import RuntimeContext


class Singleton:
    _instance = None

    @classmethod
    @default
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls, *args, **kwargs)
            cls._instance._initialized = False
        return cls._instance

    @classmethod
    @thread_bound("work")
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls, *args, **kwargs)
            cls._instance._initialized = False
        return deepcopy(cls._instance)


    # All 3 implementations (one above, 2 below) do exactly the same thing, you
    # may uncomment any of them and it will have the same result
    #
    #@thread_bound("work")
    #def __new__(cls, *args, **kwargs):
    #    thread_ctx = RuntimeContext().thread_context
    #    RuntimeContext().thread_context = RuntimeContext().default_thread_context
    #    instance = Singleton.__new__(cls, *args, **kwargs)
    #    RuntimeContext().thread_context = thread_ctx
    #    return deepcopy(instance)
    #
    #@thread_bound("work")
    #def __new__(cls, *args, **kwargs):
    #    with RuntimeContext().thread_ctx(): # argument defaults
    #                                        # to default thread context
    #        instance = Singleton.__new__(cls, *args, **kwargs)
    #    return deepcopy(instance)

    def __constructor__(self):
        self.x = 1

    def __init__(self, *args, **kwargs):
        if not self._initialized:
            self.__constructor__(*args, **kwargs)
            self._initialized = True


s = Singleton()
assert s.x == 1
s.x += 2
assert s.x == 3
Singleton().x -= 5  # change in singleton changes already gotten instance
assert s.x == -2

with RuntimeContext().thread_ctx("work"):
    s.x += 10
    assert s.x == 8
    # here we operate on deep copy
# so changes are invisible here!
assert s.x == -2