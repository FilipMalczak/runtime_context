from collections import defaultdict
from functools import wraps
from threading import current_thread
from weakref import WeakKeyDictionary


class ContextChange:
    def __init__(self, p_ctx, t_ctx):
        self.p_ctx = p_ctx
        self.t_ctx = t_ctx
        self.r_ctx = RuntimeContext()

    def __enter__(self):

        self._old_process_ctx = self.r_ctx.process_context
        self._old_thread_ctx = self.r_ctx.thread_context
        self.r_ctx.process_context = self.p_ctx
        self.r_ctx.thread_context = self.t_ctx

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.r_ctx.process_context = self._old_process_ctx
        self.r_ctx.thread_context = self._old_thread_ctx


class RuntimeContext:
    __instance = None
    def __new__(cls, *args, **kwargs):
        if cls.__instance is None:
            cls.__instance = super().__new__(cls, *args, **kwargs)
            cls.__instance._initialized = False
        return cls.__instance

    def __constructor__(self,
                        default_process_context="<p_default>",
                        default_thread_context="<t_default>"):
        self.default_process_context = default_process_context
        self.default_thread_context = default_thread_context
        self._contexts_to_foo_mapping = defaultdict(lambda :defaultdict(dict))
        self.process_context = default_process_context
        self._thread_contexts = WeakKeyDictionary() # thread weakref -> ctx name

    @property
    def thread_context(self):
        try:
            return self._thread_contexts[current_thread()]
        except KeyError:
            return self.default_thread_context

    @thread_context.setter
    def thread_context(self, value):
        self._thread_contexts[current_thread()] = value

    def __init__(self, *args, **kwargs):
        if not self._initialized:
            self.__constructor__(*args, **kwargs)
            self._initialized = True

    def drop_process_context(self, process_ctx):
        del self._contexts_to_foo_mapping[process_ctx]

    def drop_thread_context(self, thread_ctx):
        for process_ctx in self._contexts_to_foo_mapping:
            try:
                del self._contexts_to_foo_mapping[process_ctx][thread_ctx]
                if not self._contexts_to_foo_mapping[process_ctx]:
                    del self._contexts_to_foo_mapping[process_ctx]
            except KeyError:
                pass

    def drop_context(self, process_ctx, thread_ctx):
        del self._contexts_to_foo_mapping[process_ctx][thread_ctx]

    # context managers (recursively awesome)

    def context(self, process_ctx, thread_ctx):
        return ContextChange(process_ctx, thread_ctx)

    def process_ctx(self, process_ctx=None):
        if process_ctx is None:
            process_ctx = RuntimeContext().default_process_context
        return ContextChange(process_ctx, self.thread_context)

    def thread_ctx(self, thread_ctx=None):
        if thread_ctx is None:
            thread_ctx = RuntimeContext().default_thread_context
        return ContextChange(self.process_context, thread_ctx)


class ContextDependentFunction(property):
    def __init__(self, name, qualname):
        self.name = name
        self.qualname = qualname
        if not qualname.endswith("."+name):
            raise RuntimeError("Someone is cheating, qualname doesn't end with "
                               "dotted name (qualname: %s, name: %s)" %
                               (
                                   qualname,
                                   name
                               )
            )
        self.owner_name = qualname[:-(len(name)+1)]
        self.r_ctx = RuntimeContext()


    def __get__(self, instance, owner):
        try:
            foo_recognised = self.r_ctx._contexts_to_foo_mapping[self.qualname]
            try:
                process_recognised = foo_recognised[self.r_ctx.process_context]
            except KeyError:
                process_recognised = foo_recognised \
                    [self.r_ctx.default_process_context]
            try:
                thread_recognised = process_recognised \
                    [self.r_ctx.thread_context]
            except KeyError:
                try:
                    thread_recognised = process_recognised \
                        [self.r_ctx.thread_context]
                except KeyError:
                    thread_recognised = foo_recognised \
                        [self.r_ctx.default_process_context] \
                            [self.r_ctx.thread_context]
            @wraps(thread_recognised)
            def out(*args, **kwargs):
                return thread_recognised(self, *args, **kwargs)
            return out
        except KeyError:
            if instance is None:
                msg = "type object '%s' has no attribute '%s'"
            else:
                msg = "'%s' object has no attribute '%s'"
            msg = msg % (owner.__name__, self.name)
            raise AttributeError(msg)


    #def __set__... #todo
    # what should happen at monkey patching?
