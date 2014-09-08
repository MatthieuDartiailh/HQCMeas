# -*- coding: utf-8 -*-
# =============================================================================
# module : pulses/pulse.py
# author : Matthieu Dartiailh
# license : MIT license
# =============================================================================
from atom.api import (Instance, Str, Enum, Typed, Property, set_default)
import numpy as np

from hqc_meas.utils.atom_util import member_from_str
from .shapes.base_shapes import AbstractShape
from .shapes.modulation import Modulation
from item import Item


class Pulse(Item):
    """ Represent a pulse to perfom during a sequence.

    """
    # --- Public API ----------------------------------------------------------

    #: The kind of pulse can be either logical or ananlogical.
    kind = Enum('logical', 'analogical').tag(pref=True)

    #: Channel of the executioner which should perfom the pulse.
    channel = Str().tag(pref=True)

    #: Waveform
    waveform = Property()

    #: Modulation to apply to the pulse. Only enabled in analogical mode.
    modulation = Typed(Modulation, ()).tag(pref=True)

    #: Shape of the pulse. Only enabled in analogical mode.
    shape = Instance(AbstractShape).tag(pref=True)

    linkable_vars = set_default(['start', 'stop', 'duration'])

    def eval_entries(self, root_vars, sequence_locals, missings, errors):
        """ Attempt to eval the string parameters of the pulse.

        Parameters
        ----------
        root_vars : dict
            Dictionary of global variables for the all items. This will
            tipically contains the i_start/stop/duration and the root vars.

        sequence_locals : dict
            Dictionary of variables whose scope is limited to this item
            parent.

        missings : set
            Set of unfound local variables.

        errors : dict
            Dict of the errors which happened when performing the evaluation.

        Returns
        -------
        flag : bool
            Boolean indicating whether or not the evaluation succeeded.

        """
        success = super(Pulse, self).eval_entries(root_vars, sequence_locals,
                                                  missings, errors)

        if self.kind == 'analogical':
            success &= self.modulation.eval_entries(root_vars, sequence_locals,
                                                    missings, errors,
                                                    self.index)

            success &= self.shape.eval_entries(root_vars, sequence_locals,
                                               missings, errors, self.index)

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
