# -*- coding: utf-8 -*-
#==============================================================================
# module : base_shapes.py
# author : Matthieu Dartiailh
# license : MIT license
#==============================================================================
from atom.api import (Str, FloatRange)

from hqc_meas.utils.atom_util import HasPrefAtom
from ..entry_eval import eval_entry


class AbstractShape(HasPrefAtom):
    """
    """

    def eval_entries(self, sequence_locals, missing, errors, index):
        """ Evaluate the entries defining the shape.

        Parameters
        ----------
        sequence_locals : dict
            Known locals variables for the pulse sequence.

        missing : set
            Set of variables missing to evaluate some entries in the sequence.

        errors : dict
            Errors which occurred when trying to compile the pulse sequence.

        index : int
            Index of the pulse to which this shape object belongs.

        Returns
        -------
        result : bool
            Flag indicating whether or not the evaluation succeeded.

        """
        return True

    def compute(self, time, unit):
        """ Computes the shape of the pulse at a given time.

        Parameters
        ----------
        time : float
            Time at which to compute the modulation.

        unit : str
            Unit in which the time is expressed.

        Returns
        -------
        shape : float
            Amplitude of the pulse at the given time.

        """
        raise NotImplementedError('')


class SquareShape(AbstractShape):
    """ Basic square pulse with a variable amplitude.

    """

    amplitude = Str('1.0').tag(pref=True)

    def eval_entries(self, sequence_locals, missing, errors, index):
        """ Evaluate the amplitude of the pulse.

        Parameters
        ----------
        sequence_locals : dict
            Known locals variables for the pulse sequence.

        missing : set
            Set of variables missing to evaluate some entries in the sequence.

        errors : dict
            Errors which occurred when trying to compile the pulse sequence.

        index : int
            Index of the pulse to which this shape object belongs.

        Returns
        -------
        result : bool
            Flag indicating whether or not the evaluation succeeded.

        """
        prefix = '{}_'.format(index) + 'shape_'

        # Computing amplitude
        amp = None
        try:
            amp = eval_entry(self.amplitude, sequence_locals, missing)
        except Exception as e:
            errors[prefix + 'amplitude'] = repr(e)

        if amp is not None:
            self._amplitude = amp
            sequence_locals[prefix + 'amplitude'] = amp
            return True

        else:
            return False

    def compute(self, time, unit):
        """ Computes the shape of the pulse at a given time.

        Parameters
        ----------
        time : float
            Time at which to compute the modulation.

        unit : str
            Unit in which the time is expressed.

        Returns
        -------
        shape : float
            Amplitude of the pulse at the given time.

        """
        return self._amplitude

    #--- Private API ----------------------------------------------------------

    _amplitude = FloatRange(-1.0, 1.0, 1.0)
