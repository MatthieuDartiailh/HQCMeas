# -*- coding: utf-8 -*-
# =============================================================================
# module : pulses/pulse.py
# author : Matthieu Dartiailh
# license : MIT license
# =============================================================================
from atom.api import (Instance, Str, Enum, Float, Typed, Property, set_default)
import numpy as np

from hqc_meas.utils.atom_util import member_from_str
from .shapes.base_shapes import AbstractShape
from .shapes.modulation import Modulation
from .entry_eval import eval_entry
from item import Item


class Pulse(Item):
    """ Represent a pulse to perfom during a sequence.

    """
    # --- Public API ----------------------------------------------------------

    #: The kind of pulse can be either logical or ananlogical.
    kind = Enum('logical', 'analogical').tag(pref=True)

    #: Channel of the executioner which should perfom the pulse.
    channel = Str().tag(pref=True)

    #: Mode defining how the def_1 and def_2 attrs shiould be interpreted.
    def_mode = Enum('Start/Stop',
                    'Start/Duration',
                    'Duration/Stop').tag(pref=True)

    #: String representing the pulse first element of definition : according
    #: to the selected mode it evaluated value will either be used for the
    #: start instant, or duration of the pulse.
    def_1 = Str().tag(pref=True)

    #: String representing the pulse second element of definition : according
    #: to the selected mode it evaluated value will either be used for the
    #: duration, or stop instant of the pulse.
    def_2 = Str().tag(pref=True)

    linkable_vars = set_default(['start', 'stop', 'duration'])

    #: Actual start instant of the pulse with respect to the beginning of the
    #: sequence. The unit of this time depends of the setting of the context.
    start = Float()

    #: Actual duration of the pulse. The unit of this time depends of the
    #: setting of the context.
    duration = Float()

    #: Actual stop instant of the pulse with respect to the beginning of the
    #: sequence. The unit of this time depends of the setting of the context.
    stop = Float()

    #: Waveform
    waveform = Property()

    #: Modulation to apply to the pulse. Only enabled in analogical mode.
    modulation = Typed(Modulation, ()).tag(pref=True)

    #: Shape of the pulse. Only enabled in analogical mode.
    shape = Instance(AbstractShape).tag(pref=True)

    def eval_entries(self, sequence_locals, missings, errors):
        """ Attempt to eval the string parameters of the pulse.

        The string parameters are def_1, def_2 and all the parameters of the
        modulation and shape if pertinent.

        Parameters
        ----------
        sequence_locals : dict
            Dictionary of local variables.

        missings : set
            Set of unfound local variables.

        errors : dict
            Dict of the errors which happened when performing the evaluation.

        Returns
        -------
        flag : bool
            Boolean indicating whether or not the evaluation succeeded.

        """
        # Flag indicating good completion.
        success = True

        # Reference to the sequence context.
        context = self.root.context

        # Name of the parameter which will be evaluated.
        par1 = self.def_mode.split('/')[0].lower()
        par2 = self.def_mode.split('/')[1].lower()
        prefix = '{}_'.format(self.index)

        # Evaluation of the first parameter.
        d1 = None
        try:
            d1 = eval_entry(self.def_1, sequence_locals, missings)
            d1 = context.check_time(d1)
        except Exception as e:
            errors[prefix + par1] = repr(e)

        # Check the value makes sense as a start time or duration.
        if d1 is not None and d1 >= 0 and (par1 == 'start' or d1 != 0):
            setattr(self, par1, d1)
            sequence_locals[prefix + par1] = d1
        elif d1 is None:
            success = False
        else:
            success = False
            if par1 == 'start':
                m = 'Got a strictly negative value for start: {}'.format(d1)

            else:
                m = 'Got a negative value for duration: {}'.format(d1)

            errors[prefix + par1] = m

        # Evaluation of the second parameter.
        d2 = None
        try:
            d2 = eval_entry(self.def_2, sequence_locals, missings)
            d2 = context.check_time(d2)
        except Exception as e:
            errors[prefix + par2] = repr(e)

        # Check the value makes sense as a duration or stop time.
        if d2 is not None and d2 > 0 and (par2 == 'duration' or d2 > d1):
            setattr(self, par2, d2)
            sequence_locals[prefix + par2] = d2
        elif d2 is None:
            success = False
        else:
            success = False
            if par2 == 'stop' and d2 <= 0.0:
                m = 'Got a negative or null value for stop: {}'.format(d2)
            elif par2 == 'stop':
                m = 'Got a stop smaller than start: {} < {}'.format(d1, d2)
            elif d2 <= 0.0:
                m = 'Got a negative value for duration: {}'.format(d2)

            errors[prefix + par2] = m

        # Computation of the third parameter.
        if success:
            if self.def_mode == 'Start/Duration':
                self.stop = d1 + d2
                sequence_locals[prefix + 'stop'] = self.stop
            elif self.def_mode == 'Start/Stop':
                self.duration = d2 - d1
                sequence_locals[prefix + 'duration'] = self.duration
            else:
                self.start = d2 - d1
                sequence_locals[prefix + 'start'] = self.start

        if self.kind == 'analogical':
            success &= self.modulation.eval_entries(sequence_locals, missings,
                                                    errors, self.index)

            success &= self.shape.eval_entries(sequence_locals, missings,
                                               errors, self.index)

        return success

    @classmethod
    def build_from_config(cls, config, dependencies):
        """ Create a new instance using the provided infos for initialisation.

        Parameters
        ----------
        config : dict(str)
            Dictionary holding the new values to give to the members in string
            format, or dictionnary like for instance with prefs.

        dependencies : dict
            Dictionary holding the necessary classes needed when rebuilding.

        Returns
        -------
        pulse : pulse
            Newly created and initiliazed sequence.

        Notes
        -----
        This method is fairly powerful and can handle a lot of cases so
        don't override it without checking that it works.

        """
        pulse = cls()
        for name, member in pulse.members().iteritems():

            # First we set the preference members
            meta = member.metadata
            if meta and 'pref' in meta:
                if name not in config:
                    continue

                if name not in ('modulation', 'shape'):
                    # member_from_str handle containers
                    value = config[name]
                    validated = member_from_str(member, value)

                    setattr(pulse, name, validated)

                elif name == 'modulation':
                    mod = pulse.modulation
                    mod.update_members_from_preferences(**config[name])

                else:
                    shape_config = config[name]
                    if shape_config == 'None':
                        continue
                    shape_name = shape_config.pop('shape_class')
                    shape_class = dependencies['pulses']['shapes'][shape_name]
                    shape = shape_class()
                    shape.update_members_from_preferences(**shape_config)
                    pulse.shape = shape

        return pulse

    # --- Private API ---------------------------------------------------------

    def _answer(self, members, callables):
        """ Collect the answers for the walk method.

        Dotted name are allowed for members to access either the modulation or
        shape.
        ex : 'modulation.amplitude', 'shape.shape_class'

        """
        answers = {m: getattr(self, m, None) for m in members}
        if self.kind == 'analogical':
            # Accessing modulation members.
            mod_members = [m for m in members
                           if m.startswith('modulation.')]
            answers.update({m: getattr(self.modulation, m[11:], None)
                            for m in mod_members})

            # Accessing shape members.
            sha_members = [m for m in members
                           if m.startswith('shape.')]
            answers.update({m: getattr(self.shape, m[6:], None)
                            for m in sha_members})

        answers.update({k: c(self) for k, c in callables.iteritems()})
        return answers

    def _get_waveform(self):
        """ Getter for the waveform property.

        """
        context = self.root.context
        n_points = context.len_sample(self.duration)
        if self.kind == 'analogical':
            time = np.linspace(self.start, self.stop, n_points, False)
            mod = self.modulation.compute(time, context.time_unit)
            shape = self.shape.compute(time, context.time_unit)
            return mod*shape
        else:
            return np.ones(n_points, dtype=np.int8)
