# -*- coding: utf-8 -*-
#==============================================================================
# module : base_context.py
# author : Matthieu Dartiailh
# license : MIT license
#==============================================================================
from atom.api import Enum, Str, Bool, Float, Property
from hqc_meas.utils.atom_util import HasPrefAtom

# Time conversion dictionary first key is the original unit, second the final
# one.
TIME_CONVERSION = {'s': {'s': 1, 'ms': 1e3, 'mus': 1e6, 'ns': 1e9},
                   'ms': {'s': 1e3, 'ms': 1, 'mus': 1e-3, 'ns': 1e-6},
                   'mus': {'s': 1e6, 'ms': 1e3, 'mus': 1, 'ns': 1e-3},
                   'ns': {'s': 1e9, 'ms': 1e6, 'mus': 1e3, 'ns': 3}}


class BaseContext(HasPrefAtom):
    """
    """
    #: Time unit.
    time_unit = Enum('mus', 's', 'ms', 'ns').tag(pref=True)

    #: Duration in unit of the context of a pulse. It is the responsability
    #: of subclasses to implement a getter.
    sampling_time = Property(cached=True)

    #: Whether or not to round times to the nearest multiple of sampling time
    #: when checking.
    rectify_time = Bool(True).tag(pref=True)

    #: When times are not rectified tolerance above which a time is considered
    #: to be too far from a multiple of the sampling time to be used.
    tolerance = Float(0.000000001).tag(pref=True)

    #: Name of the context class. Used for persistence purposes.
    context_class = Str().tag(pref=True)

    def compile_sequence(self, pulses, **kwargs):
        """

        """
        pass

    def len_sample(self, start, stop):
        """ Compute the number of samples between two times.

        Parameters
        ----------
        start : float
            Starting instant of the 'pulse'

        stop : float
            Last instant of th pulse (ie true last instant not last instant
            minus the sampling time).

        Returns
        -------
        length : int
            Number of samples the instr will use to represent the interval
            between start and stop

        """
        return int(round(stop - start) / self.sampling_time)

    def check_time(self, time):
        """ Check a given time can be represented by an int given the
        sampling frequency.

        """
        if time is None or time < 0:
            return time

        rectified_time = self.sampling_time*round(time/self.sampling_time)

        if self.rectify_time:
            return rectified_time

        else:
            if abs(time - rectified_time) > self.tolerance:
                raise ValueError('Time does not fit the instr resolution')
            return time

    def _default_context_class(self):
        """ Default value the context class member.

        """
        return type(self).__name__
