# -*- coding: utf-8 -*-
from enaml.layout.api import InsertItem
import enaml

from ..driver_debug_panel import DriverDebugPanel

with enaml.imports():
    from ..driver_debug_view import DriverDebugView
    
def build_debug_panel(main_panel, area):
    """
    """
    model = DriverDebugPanel(main_panel = main_panel)
    main_panel.panels.append(model)
    
    dock_numbers = sorted([pane.name[5] for pane in area.dock_items()])
    if dock_numbers and dock_numbers[-1] > len(dock_numbers):
        first_free = min(set(xrange(len(dock_numbers))) - dock_numbers)
        name = 'item_{}'.format(first_free)
    else:
        name = 'item_{}'.format(len(dock_numbers) + 1)
        
    DriverDebugView(area, model = model, name = name)
    area.update_layout(InsertItem(item = name))
    
def is_debug_active(panels):
    """
    """
    return bool(any([isinstance(p, DriverDebugPanel) for p in panels]))