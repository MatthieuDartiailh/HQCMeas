# -*- coding: utf-8 -*-
#==============================================================================
# module : database_string_formatter.py
# author : Matthieu Dartiailh
# license : MIT license
#==============================================================================
"""
"""
import textwrap
from math import (cos, sin, tan, acos, asin, atan,
                exp, log, cosh, sinh, tanh, atan2)
from cmath import pi as Pi
import numpy as np
import cmath

COMPLETER_TOOLTIP = textwrap.fill("""In this field you can enter a text and
                        include fields which will be replaced by database
                        entries by using the delimiters '{' and '}'.""", 80)


def safe_eval(expr, local_var=None):
    """
    """
    if expr.isalpha():
        return expr

    if local_var:
        return eval(expr, globals(), local_var)
    else:
        return eval(expr)


def get_formatted_string(edit_str, path, database):
    """
    """
    aux_strings = edit_str.split('{')
    if len(aux_strings) > 1:
        string_elements = [string for aux in aux_strings
                           for string in aux.split('}')]
        replacement_values = [database.get_value(path, key)
                              for key in string_elements[1::2]]
        str_to_format = ''
        for key in string_elements[::2]:
            str_to_format += key + '{}'
        if edit_str.endswith('}'):
            str_to_format = str_to_format[:-2]
        else:
            str_to_format = str_to_format[:-2]

        return str_to_format.format(*replacement_values)
    else:
        return edit_str


def format_and_eval_string(edit_str, path, database):

    aux_strings = edit_str.split('{')
    if len(aux_strings) > 1:
        string_elements = [string for aux in aux_strings
                           for string in aux.split('}')]
        replacement_token = ['_a{}'.format(i)
                             for i in xrange(len(string_elements[1::2]))]
        replacement_values = {'_a{}'.format(i): database.get_value(path, key)
                              for i, key in enumerate(string_elements[1::2])}
        str_to_format = ''
        for key in string_elements[::2]:
            str_to_format += key + '{}'
        if edit_str.endswith('}'):
            str_to_format = str_to_format[:-2]
        else:
            str_to_format = str_to_format[:-2]

        expr = str_to_format.format(*replacement_token)
        return safe_eval(expr, replacement_values)
    else:
        return safe_eval(edit_str)
