## Python stack formatter

When your only debugger is a log file, better add some extra-verbose traceback formatting (a bit more source context & current variable values).


#### Before
<img src="tb_before.png" width="400">

#### After
<img src="tb_after.png" width="400">

# Usage

## Log detailed tracebacks for exceptions
Just call `show` or `format` in an except block.

By default, this produces a plain text string. Pass `style='color'` to get semantic highlighting, see the docs of `format` for the full set of configs.

```python
import stackprinter

try:
    something()
except:
    stackprinter.show(style='color')  # grab the current exception and print it to stderr

    # ...or only return a string, e.g. for logging.
    # defaults to plain text.
    message = stackprinter.format()
    logging.log(message)
```
There's also a `stackprinter.set_excepthook`, which replaces the default python crash message (so it works everywhere without the extra `try/catch`ing).

You can also pass things like exception objects explicitely (see docs).

## See the curremt call stack of another thread
Pass the thread object to `show` or `format`

```python
thread = threading.Thread(target=something)
thread.start()
while True:
    stackprinter.show(thread) # or format()
    time.sleep(0.1)
```

## See the call stack of the current thread
```python
stackprinter.show() # or format()
```

## Trace a piece of code as it is executed

More for curiosity than anything else, you can watch a piece of code execute step-by-step, printing a trace of all function calls & returns 'live' as they are happening. Slows everything down though, of course.
```python
tp = TracePrinter(style='color', suppressed_paths=[r"lib/python.*/site-packages/numpy"])
tp.enable()
a = np.ones(111)
dosomething(a)
tp.disable()
```

<img src="trace.png" width="400">

# How it works

Basically, this is a frame formatter. For each [frame on the call stack](https://en.wikipedia.org/wiki/Call_stack), it grabs the source code to find out which source lines reference which variables. Then it displays code and variables in the neighbourhood of the last executed line. Since it knows where in the code each variable occurs, it's relatively easy to do semantic highlighting.

The frame inspection routines are independent of any actual string formatting, so it should be fairly straightforward to write other formatter types on top. Like, foldable and clickable html pages instead of text logs, with download links for pickled variable contents?

# Caveats

This displays variable values as they are _at the time of formatting_. In
multi-threaded programs, variables can change while we are busy walking
the stack & printing them. So, if nothing seems to make sense, consider that
your exception and the traceback messages are from slightly different times.
Sadly, there is no responsible way to freeze all other threads as soon
as we want to inspect some thread's call stack (...or is there?)

# Docs

\*coughs\*

For now, look at the doc strings