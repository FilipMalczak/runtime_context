RuntimeContext
==============

Situation
---------

Let's look at multi-threaded (or multi-processed) application.

Each Process is a single thread of execution (possibly locked, waiting for
synchronization), and it shares memory with other threads of execution - Threads.

If we use many processes we need to synchronize data and control flow between
them with high level constructs (like Lock, Semaphore, etc). No memory is
automatically shared, which means that we need to take care of serialization and
keeping consistency of data between processes.

I like to call single Process with its Threads a Runtime. There is some coding
philosophy (which I am great fan of), where you create runtime, in which there
are "floating" data and logic packs, accessible from any place in program with
its name only (Singleton pattern) or with its name and some key (Flyweight
pattern).

Examples of such "data and logic" packs (or just "objects") may be
Config or Session singletons (keeping track of loaded config, or session
history - we want them to be single instances in the whole runtime, so we can
check config content, or update session statistics from any place in program).

Now, lets say that you have application, where:
- main thread (process thread) spawns worker threads, which go idle and wait for
  data in some queue; main thread takes users input and according to it, starts
  new job (adds it to queue), or changes global job parameters (in some
  singleton, lets call it Variables for a moment)
- worker threads wait for something to come up from a shared queue, consumes it
  (so no other worker uses the same element), and does some job on it, using
  parameters from Variables singleton.

Assume that worker threads are just "runners" for job executors, and job
executors are somehow loaded plugins, provided by user. For example, users input
may be simple mathematical formulas like "1+2" or "c-3" or pseudo-variables
binding, like "c=5". Workers should parse users input, choose some plugin
(Adder, Substractor, Multiplier, etc) and use it for calculating formulas,
or bind pseudo-variables (stored in Variables singleton) itself.

Problem
-------

Now, lets imagine some rouge plugin-writing user. Our nice user inputs all kind
of stuff into program (`"a=3"`, `"b-5"`, `"delta=500"`, `"c*d"`, etc), and some
of those operations (those, which evaluates to number, and has no side effects)
are handled by plugins.

So what happens when rouge plugin writer creates plugin, that takes input that
shouldn't have side effects and GIVES IT SIDE EFFECTS? We may come up with
such situation:

> `x = 5   # user input, binds x to 5`

> `x - 1   # user input, returns 4, but ALSO changes x to 3`

> `x - 1   # user input, we expect it to return 4 again, but it returns 2!`

So, we need a way to isolate plugin execution from rest of runtime. This is
where runtime context comes to play, and why I wrote this already-know-it piece
on threads and processes.

Approach
--------

My approach is to create singleton taking care of runtime context.

Context itself is just a name, but every Thread may have its own context at the
moment, and the whole process may have its context.

I provide some tools (at the moment only decorator for functions) which allows
you to specify objects behaviour depending on thread or process context.

How does it work? We decorate many implementations of the same function (one
qualname defines one function) with context binding. We may specify, that some
implementation should be used, when we are in some thread-wide context, or (if
we use default thread-wide context) in some process-wide context. We may also
specify that specific implementation should be used only when we are in given
process-wide context AND given thread-wide context.

Now, we can change context (thread- or process-wide) and function will be chosen
according to chosen context (in the runtime).

Example (basing on our problem)
-------------------------------

So,lets head back to our problem described above.

We can deal with rouge plugin writers in very simple fashion. We'll probably
implement singletons by overriding some method, that returns its instance (and
creates it, if there is None), probably `__new__`.

Now, we bind standard construction method to default context, so default
behaviour will be that of standard singleton. Additional step is binding
function that instead of existing instance, returns deep copy of it, and bind
it to thread-wide "plugin-work" context. Both of this implementations should
have the same qualified name.

Now, in worker thread, just before calling plugin method, we switch thread-wide
context to "plugin-work", and just after its execution, we switch back to
default.

What happens here? Main Thread is in default context all the time, so it has
standard access to singleton, and can change its contents. Worker Threads will
have the same access most of the time, but when we switch context, the same call
that returned singleton instance a moment ago, now returns its copy, so plugins
may change its contents (for example for storing temporary variables), without
any side effects after switching to default context.

This solution is simplified and showed in "singleton_example" module.

Project status
--------------

VERY WIP. I've spent about 5 hours of work on this, thats not much. Existing
code is stubby, undocumented, and won't work for standard functions (not
methods).

Aaaand... Singleton example doesn't work. Well, shit happens, gonna need work.

Ideas
-----

- thread grouping and group context
- support for simple functions
- support for multiprocessing