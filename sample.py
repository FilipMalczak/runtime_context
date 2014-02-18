from contexting_lib.decorators import default, thread_bound, process_bound, context_bound
from contexting_lib.runtime_context import RuntimeContext


class A:
    @default
    def foo(self):
        print("def")

    @thread_bound("at")
    def foo(self):
        print("at")

    @process_bound("ap")
    def foo(self):
        print("ap")

    @context_bound("app", "tpp")
    def foo(self):
        print("app/tpp")

a = A()

r_ctx = RuntimeContext()
a.foo()
r_ctx.thread_context = "at"
a.foo()
r_ctx.thread_context = r_ctx.default_thread_context
r_ctx.process_context = "ap"
a.foo()
r_ctx.thread_context = "tpp"
r_ctx.process_context = "app"
a.foo()
r_ctx.process_context = "x"
try:
    a.foo()
    raise Exception()
except AttributeError:
    print("passed")

with r_ctx.thread_ctx("at"):
    a.foo()

#STDOUT:
#def
#at
#ap
#app/tpp
#passed
#at


