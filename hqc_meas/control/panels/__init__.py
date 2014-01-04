# -*- coding: utf-8 -*-

import enaml

if 'SINGLE_INSTR_VIEWS' not in globals():
    import os.path, importlib
    dir_path = os.path.dirname(__file__)
    SINGLE_INSTR_VIEWS = {}
    modules = ['.' + os.path.split(path)[1][:-6] 
                for path in os.listdir(dir_path)
                    if path.endswith('.enaml')]
    with enaml.imports():
        for module in modules:
            mod = importlib.import_module(module, __name__)
            SINGLE_INSTR_VIEWS.update(getattr(mod, 'SINGLE_INSTR_VIEWS'))