# -*- coding: utf-8 -*-
# =============================================================================
# module : tests/pulses/template_makers.py
# author : Matthieu Dartiailh
# license : MIT license
# =============================================================================
"""

"""
from hqc_meas.pulses.pulse import Pulse
from hqc_meas.pulses.base_sequences import RootSequence, Sequence
from hqc_meas.pulses.shapes.base_shapes import SquareShape
from hqc_meas.pulses.contexts.template_context import TemplateContext


def create_template_sequence():
    root = RootSequence()
    context = TemplateContext(logical_channels=['A', 'B'],
                              analogical_channels=['Ch1', 'Ch2'],
                              channel_mapping={'A': '', 'B': '', 'Ch1': '',
                                               'Ch2': ''})
    root.context = context
    root.local_vars = {'a': '1.5'}

    pulse1 = Pulse(channel='A', def_1='1.0', def_2='{a}')
    pulse2 = Pulse(channel='B', def_1='{a} + 1.0', def_2='3.0')
    pulse3 = Pulse(channel='Ch1', def_1='{2_stop} + 0.5', def_2='{b}',
                   kind='Analogical', shape=SquareShape())
    seq = Sequence(items=[Pulse(channel='Ch2',
                                def_1='{2_stop} + 0.5', def_2='{sequence_end}',
                                kind='Analogical', shape=SquareShape())])
    root.items.extend([pulse1, pulse2, seq,  pulse3])

    pref = root.preferences_from_members()
    pref['template_vars'] = repr(dict(b=''))
    del pref['item_class']
    del pref['external_vars']
    del pref['time_constrained']
    return pref
