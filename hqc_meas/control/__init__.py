# -*- coding: utf-8 -*-
"""

"""
if 'SINGLE_INSTR_PANELS' not in globals():
    import os.path, importlib
    SINGLE_INSTR_PANELS = {}
    dir_path = os.path.dirname(__file__)
    modules = ['.' + os.path.split(path)[1][:-3] 
                for path in os.listdir(dir_path)
                    if path.endswith('.py')]
    for module in modules:
        mod = importlib.import_module(module, __name__)
        SINGLE_INSTR_PANELS.update(getattr(mod, 'SINGLE_INSTR_PANELS'))