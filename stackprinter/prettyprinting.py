import os
import pprint

from stackprinter.extraction import UnresolvedAttribute
from stackprinter.utils import inspect_callable

try:
    import numpy as np
except ImportError:
    np = False

MAXLEN_DICT_KEY_REPR = 25
MAX_LIST_ENTRIES = 9000



def format_value(value, indent=0, truncation=None, wrap=60, max_depth=2, depth=0):

    # TODO see how pprint could be used instead https://docs.python.org/3/library/pprint.html
    # (but how to extend for e.g. custom array printing?)

    if depth > max_depth:
        return '...'

    if isinstance(value, UnresolvedAttribute):
        reason = "# %s" % (value.exc_type)
        val_tpl = reason + "\n%s = %s"
        lastval_str = format_value(value.last_resolvable_value, truncation=truncation, indent=3, depth=depth+1)
        val_str = val_tpl % (value.last_resolvable_name, lastval_str)
        indent = 10

    elif isinstance(value, list):
        val_str = format_iterable(value, '[', ']', truncation, max_depth, depth)

    elif isinstance(value, tuple):
        val_str = format_iterable(value, '(', ')', truncation, max_depth, depth)

    elif isinstance(value, set):
        val_str = format_iterable(value, '{', '}', truncation, max_depth, depth)

    elif isinstance(value, dict):
        # TODO write what type of dict specialization it is via value.__class__.__name__
        if depth == max_depth:
            val_str = '{...}'
        else:
            vstrs = []
            for k, v in value.items():
                kstr = truncate(repr(k), MAXLEN_DICT_KEY_REPR)
                vstr = format_value(v, indent=len(kstr)+3, truncation=truncation, depth=depth+1)
                vstrs.append("%s: %s" % (kstr, vstr))
            val_str = '{' + ',\n '.join(vstrs) + '}'

    elif np and isinstance(value, np.ndarray):
        val_str = format_array(value, minimize=depth > 0)

    elif callable(value):
        name, filepath, method_owner, ln = inspect_callable(value)
        filename = os.path.basename(filepath) if filepath is not None else None
        if filename is None:
            val_str = safe_repr(value)
        elif method_owner is None:
            name_s = safe_str(name)
            filename_s = safe_str(filename)
            ln_s = safe_str(ln)
            val_str = "<function '%s' %s:%s>" % (name_s, filename_s, ln_s)
        else:
            name_s = safe_str(name)
            filename_s = safe_str(filename)
            method_owner_s = safe_str(method_owner)
            ln_s = safe_str(ln)
            val_str = "<method '%s' of %s %s:%s>" % (name_s, method_owner_s, filename_s, ln_s)

    # maybe just try: repr(value), because try: str(value) may already be implied (doublecheck)
    else:
        val_str= safe_repr_or_str(value)

    val_str = truncate(val_str, truncation)

    if depth == 0:
        val_str = wrap_lines(val_str, wrap)

    if indent > 0:
        nl_indented = '\n' + (' ' * indent)
        val_str = val_str.replace('\n', nl_indented)


    return val_str


def safe_repr(value):
    try:
        return repr(value)
    except:
        return '# error calling repr'

def safe_str(value):
    try:
        return str(value)
    except:
        return '# error calling str'

def safe_repr_or_str(value):
    try:
        return repr(value)
    except:
        try:
            return str(value)
        except:
            return '# error calling repr or str'

def format_iterable(value, prefix, postfix, truncation, max_depth, depth):
    # TODO cleanup

    # TODO always write class name if it isn't base list, base tuple
    length = len(value)
    val_str = prefix
    if depth == max_depth:
        val_str += '...'
    else:
        linebreak = False
        i = 0
        for v in value:
            i += 1
            if i > MAX_LIST_ENTRIES:
                break
            entry = format_value(v, indent=1, truncation=truncation, depth=depth+1)
            sep = ', ' if i < length else ''
            if '\n' in entry:
                val_str += "\n %s%s" % (entry, sep)
                linebreak = True
            else:
                if linebreak:
                    val_str += '\n'
                    linebreak = False
                val_str += "%s%s" % (entry, sep)

    val_str += postfix

    if len(val_str) > 100 or depth == max_depth:
        dtype = value.__class__.__name__
        sep = '\n' if depth < max_depth else ' '
        val_str = "%s-%s:%s%s" % (length, dtype, sep, val_str)
    return val_str


def format_array(arr, minimize=False):
    if arr.ndim >= 1:
        shape = list(arr.shape)
        if len(shape) < 2:
            shape.append('')
        shape_str = "x".join(str(d) for d in shape)
        if len(shape_str) < 10:
            prefix = "%s array(" % shape_str
            msg = prefix
        else:
            prefix = ""
            msg = "%s array(\n" % shape_str
    else:
        msg = prefix = "array("

    suffix = ')'

    array_rep = np.array2string(arr, max_line_width=9000, threshold=50,
                        edgeitems=2, prefix=prefix, suffix=suffix)

    if minimize and (len(array_rep) > 50 or arr.ndim > 1):
        array_rep = "%s%s...%s" % ('[' * arr.ndim, arr.flatten()[0], ']' * arr.ndim)


    msg += array_rep + suffix
    return msg


def truncate(string, n):
    if not n:
        return string
    n = max(n, 0)
    if len(string) > (n+3):
        string = "%s..." % string[:n].rstrip()
    return string


def wrap_lines(string, max_width=80):

    def wrap(lines):
        for l in lines:
            length = len(l)
            if length <= max_width:
                yield l
            else:
                k = 0
                while k < length:
                    snippet = l[k:k+max_width]
                    if k > 0:
                        snippet = " " + snippet

                    yield snippet
                    k += max_width

    wrapped_lines = wrap(string.splitlines())
    return '\n'.join(wrapped_lines)