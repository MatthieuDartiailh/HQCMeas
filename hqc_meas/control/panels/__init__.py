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
    modules.remove('.__init__')
    for module in modules:
        mod = importlib.import_module(module, __name__)
        aux = getattr(mod, 'SINGLE_INSTR_PANELS')
        
        for key in aux:
            
            if key not in SINGLE_INSTR_PANELS:
                SINGLE_INSTR_PANELS[key] = []
                
            SINGLE_INSTR_PANELS[key].extend(aux[key])