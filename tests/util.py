# -*- coding: utf-8 -*-


def complete_line(string, char, length=79):
    str_len = len(string)
    if str_len < length-1:
        return string + ' ' + ''.join([char for i in range(length-1-str_len)])
    else:
        return string
