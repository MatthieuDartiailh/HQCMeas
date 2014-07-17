# -*- coding: utf-8 -*-
# =============================================================================
# module : loop_exceptions.py
# author : Matthieu Dartiailh
# license : MIT license
# =============================================================================
"""
"""


class LoopException(BaseException):
    pass


class BreakException(LoopException):
    """ Exception used to signal a looping task it should break.

    """
    pass


class ContinueException(LoopException):
    """ Exception used to signal a looping task it should continue.

    """
    pass
