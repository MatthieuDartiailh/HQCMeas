# -*- coding: utf-8 -*-

import enaml

if 'SINGLE_INSTR_VIEWS' not in globals():
    import os.path, importlib
    dir_path = os.path.dirname(__file__)
    SINGLE_INSTR_VIEWS = {'main' : [],
                          'aux' : [],
                          'prop' : []}
    modules = ['.' + os.path.split(path)[1][:-6] 
                for path in os.listdir(dir_path)
                    if path.endswith('.enaml')]
    with enaml.imports():
        for module in modules:
            mod = importlib.import_module(module, __name__)
            aux  = getattr(mod, 'SINGLE_INSTR_VIEWS')
            SINGLE_INSTR_VIEWS['main'].extend(aux.get('main', []))
            SINGLE_INSTR_VIEWS['aux'].extend(aux.get('aux', []))
            SINGLE_INSTR_VIEWS['prop'].extend(aux.get('prop', []))