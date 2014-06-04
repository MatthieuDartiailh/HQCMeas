# -*- coding: utf-8 -*-
#==============================================================================
# module : eval_entry.py
# author : Matthieu Dartiailh
# license : MIT license
#==============================================================================
from math import cos, sin, tan, acos, asin, atan, exp, log, log10
import cmath as cm
import numpy as np
from math import pi as Pi


def safe_eval(expr, local_var=None):
    """
    """
    if expr.isalpha():
        return expr

    if local_var:
        return eval(expr, globals(), local_var)
    else:
        return eval(expr)


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
        str_to_eval = ''
        for key in elements[::2]:
            str_to_eval += key + '{}'
        str_to_eval = str_to_eval[:-2]

        expr = str_to_eval.format(*replacement_token)
        return safe_eval(expr, replacement_values)
    else:
        return safe_eval(string)
