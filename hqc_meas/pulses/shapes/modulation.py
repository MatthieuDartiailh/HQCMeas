# -*- coding: utf-8 -*-
from atom.api import (Str, Enum, Float, Bool, FloatRange)
from math import cos, sin
from math import pi as Pi

from hqc_meas.utils.atom_util import HasPrefAtom
from ..entry_eval import eval_entry

FREQ_TIME_UNIT_MAP = {'s': {'Hz': 1, 'kHz': 1000, 'MHz': 1e6, 'GHz': 1e9},
                      'ms': {'Hz': 1e-3, 'kHz': 1, 'MHz': 1e3, 'GHz': 1e6},
                      'mus': {'Hz': 1e-6, 'kHz': 1e-3, 'MHz': 1, 'GHz': 1e3},
                      'ns': {'Hz': 1e-9, 'kHz': 1e-6, 'MHz': 1e-3, 'GHz': 1}}


class Modulation(HasPrefAtom):
    """ Modulation to apply to the pulse.

    Only sinusoïdal and cosinusoïdal modulations are supported. As the
    modulation is applied on top of the shape is more complicated modulation
    are requested they can be implemented in cutom shapes.

    """
    #: Flag indicating whether or not the modulation is activated.
    activated = Bool().pref(pref=True)

    #: Kind of modulation to use : cos or sin
    kind = Enum('cos', 'sin').tag(pref=True)

    #: Relative amplitude of the modulation.
    amplitude = Str().tag(pref=True)

    #: Frequency of modulation to use.
    frequency = Str().tag(pref=True)

    #: Unit of the frequency use for the modulation.
    frequency_unit = Enum('MHz', 'GHz', 'kHz', 'Hz').tag(pref=True)

    #: Phase to use in the modulation.
    phase = Str().tag(pref=True)

    #: Unit of the phase used in the modulation.
    phase_unit = Enum('rad', 'deg').tag(pref=True)

    def eval_entries(self, sequence_locals, missing):
        """ Evaluate amplitude, frequency, and phase.

        """
        evals = {}
        errs = []
        try:
            amp = eval_entry(self.amplitude, sequence_locals, missing)
        except Exception as e:
            eval_success = False
            errs.append(repr(e))

        if amp is not None:
            self._amplitude = amp
            evals['amplitude'] = amp

        try:
            freq = eval(self.frequency, globals(), sequence_locals)
            self._frequency = freq
        except Exception:
            eval_success = False
            errs.append(repr(e))

        try:
            phase = eval(self.frequency, globals(), sequence_locals)
            self._phase = phase
        except Exception:
            eval_success = False
            errs.append(repr(e))

        return eval_success

    def compute(self, time, unit):
        """

        """
        if not self.activated:
            return 1

        unit_corr = 2*Pi*FREQ_TIME_UNIT_MAP[unit][self.frequency_unit]
        phase = self._phase
        if self.phase_unit == 'deg':
            phase *= 2*Pi

        if self.kind == 'sin':
            return self._amplitude*sin(unit_corr*self._frequency*time + phase)
        else:
            return self._amplitude*cos(unit_corr*self._frequency*time + phase)

    #--- Private API ----------------------------------------------------------

    _amplitude = FloatRange(-1.0, 1.0, 1.0)

    _frequency = Float()

    _phase = Float()
