# -*- coding: utf-8 -*-
#==============================================================================
# module : __init__.py
# author : Matthieu Dartiailh
# license : MIT license
#==============================================================================

import enaml
with enaml.imports():
    from process_engine_manifest import ProcessEngineManifest

ENGINES = [ProcessEngineManifest]
