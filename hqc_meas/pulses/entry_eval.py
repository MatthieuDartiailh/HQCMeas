# -*- coding: utf-8 -*-
# =============================================================================
# module : eval_entry.py
# author : Matthieu Dartiailh
# license : MIT license
# =============================================================================
from math import cos, sin, tan, acos, asin, atan, exp, log, log10
import cmath as cm
import numpy as np
from math import pi as Pi
from inspect import cleandoc
from textwrap import fill
from future.utils import exec_


EVALUATER_TOOLTIP = '\n'.join([
    fill(cleandoc("""In this field you can enter a text and
                  include fields which will be replaced by database
                  entries by using the delimiters '{' and '}' and
                  which will then be evaluated."""), 80),
    "Available math functions:",
    "- cos, sin, tan, acos, asin, atan, atan2",
    "- exp, log, log10, cosh, sinh, tanh, sqrt",
    "- complex math function are available under cm",
    "- numpy function are avilable under np",
    "- pi is available as Pi"])


def eval_entry(string, seq_locals, missing_locals):
    """

    """
    aux_strings = string.split('{')
    if len(aux_strings) > 1:
        elements = [el for aux in aux_strings
                    for el in aux.split('}')]

        missing = [el for el in elements[1::2] if el not in seq_locals]
        if missing:
            missing_locals.update(set(missing))
            return None

        replacement_token = ['_a{}'.format(i)
                             for i in xrange(len(elements[1::2]))]
        replacement_values = {'_a{}'.format(i): seq_locals[key]
                              for i, key in enumerate(elements[1::2])}

        str_to_eval = ''.join(key + '{}' for key in elements[::2])
        str_to_eval = str_to_eval[:-2]

        expr = str_to_eval.format(*replacement_token)
    else:
        replacement_values = {}
        expr = string

    return eval(expr, globals(), replacement_values)


def exec_entry(string, seq_locals, missing_locals):
    """

    """
    aux_strings = string.split('{')
    if len(aux_strings) > 1:
        elements = [el for aux in aux_strings
                    for el in aux.split('}')]

        missing = [el for el in elements[1::2] if el not in seq_locals]
        if missing:
            missing_locals.update(set(missing))
            return None

        replacement_token = ['_a{}'.format(i)
                             for i in xrange(len(elements[1::2]))]
        replacement_values = {'_a{}'.format(i): seq_locals[key]
                              for i, key in enumerate(elements[1::2])}

        str_to_eval = ''.join(key + '{}' for key in elements[::2])
        str_to_eval = str_to_eval[:-2]

        expr = str_to_eval.format(*replacement_token)
    else:
        replacement_values = {}
        expr = string

    exec_(expr, locs=replacement_values)
    return locals()
