# -*- coding: utf-8 -*-
# =============================================================================
# module : base_shapes.py
# author : Matthieu Dartiailh
# license : MIT license
# =============================================================================
from atom.api import (Str, FloatRange, Float)
import numpy as np

from hqc_meas.utils.atom_util import HasPrefAtom
from ..entry_eval import eval_entry


class AbstractShape(HasPrefAtom):
    """
    """

    shape_class = Str().tag(pref=True)

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
        time : ndarray
            Times at which to compute the modulation.

        unit : str
            Unit in which the time is expressed.

        Returns
        -------
        shape : ndarray
            Amplitudes of the pulse at the given time.

        """
        raise NotImplementedError('')

    def _default_shape_class(self):
        return type(self).__name__

    def _answer(self, members, callables):
        """ Collect answers for the walk method.

        """
        answers = {m: getattr(self, m, None) for m in members}
        answers.update({k: c(self) for k, c in callables.iteritems()})
        return answers


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
            return True

        else:
            return False

    def compute(self, time, unit):
        """ Computes the shape of the pulse at a given time.

        Parameters
        ----------
        time : ndarray
            Times at which to compute the modulation.

        unit : str
            Unit in which the time is expressed.

        Returns
        -------
        shape : ndarray
            Amplitude of the pulse.

        """
        return self._amplitude*np.ones(len(time))

    # --- Private API ---------------------------------------------------------

    _amplitude = FloatRange(-1.0, 1.0, 1.0)


class GaussianShape(AbstractShape):
    """ Basic gaussian pulse with a variable amplitude.

    """

    amplitude = Str('1.0').tag(pref=True)
    center = Str('').tag(pref=True)
    width = Str('').tag(pref=True)

    def eval_entries(self, sequence_locals, missing, errors, index):
        """ Evaluate the amplitude, width and center position of the pulse.

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

        # Computing amplitude, width and center
        amp = None
        width = None
        center = None
        try:
            amp = eval_entry(self.amplitude, sequence_locals, missing)
            width = eval_entry(self.width, sequence_locals, missing)
            center = eval_entry(self.center, sequence_locals, missing)

        except Exception as e:
            errors[prefix + 'amplitude'] = repr(e)
            errors[prefix + 'width'] = repr(e)
            errors[prefix + 'center'] = repr(e)
        if amp is not None:
            self._amplitude = amp
            if width is not None:
                self._width = width
                if center is not None:
                    self._center = center
                    return True
        else:
            return False


    def compute(self, time, unit):
        """ Computes the shape of the pulse at a given time.

        Parameters
        ----------
        time : ndarray
            Times at which to compute the modulation.

        unit : str
            Unit in which the time is expressed.

        Returns
        -------
        shape : ndarray
            Amplitude of the pulse.

        """
        return float(self._amplitude)*np.exp(-np.square(time-self._center)/(2.0*self._width**2))

    # --- Private API ---------------------------------------------------------

    _amplitude = FloatRange(-1.0, 1.0, 1.0)
    _width = Float()
    _center = Float()

SHAPES = [SquareShape, GaussianShape]
