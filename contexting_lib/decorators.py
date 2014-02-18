from contexting_lib.runtime_context import ContextDependentFunction, RuntimeContext

def default(foo):
    runtime_context = RuntimeContext()
    def_p_ctx = runtime_context.default_process_context
    def_t_ctx = runtime_context.default_thread_context
    runtime_context._contexts_to_foo_mapping \
        [foo.__qualname__] \
            [def_p_ctx] \
                [def_t_ctx] = foo
    return ContextDependentFunction(foo.__name__, foo.__qualname__)


def thread_bound(thread_context):
    def decorator(foo):
        runtime_context = RuntimeContext()
        def_p_ctx = runtime_context.default_process_context
        runtime_context._contexts_to_foo_mapping \
            [foo.__qualname__] \
                [def_p_ctx] \
                    [thread_context] = foo
        return ContextDependentFunction(foo.__name__, foo.__qualname__)
    return decorator


def process_bound(process_context):
    def decorator(foo):
        runtime_context = RuntimeContext()
        def_t_ctx = runtime_context.default_thread_context
        runtime_context._contexts_to_foo_mapping \
            [foo.__qualname__] \
                [process_context] \
                    [def_t_ctx] = foo
        return ContextDependentFunction(foo.__name__, foo.__qualname__)
    return decorator


def context_bound(process_context, thread_context):
    def decorator(foo):
        runtime_context = RuntimeContext()
        runtime_context._contexts_to_foo_mapping \
            [foo.__qualname__] \
                [process_context] \
                    [thread_context] = foo
        return ContextDependentFunction(foo.__name__, foo.__qualname__)
    return decorator