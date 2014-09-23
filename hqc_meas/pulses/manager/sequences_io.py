# -*- coding: utf-8 -*-
# =============================================================================
# module : hqc_meas/pulses/manager/sequences_io.py
# author : Matthieu Dartiailh
# license : MIT license
# =============================================================================
"""
"""
from configobj import ConfigObj
from textwrap import wrap


def load_sequence_prefs(path):
    """ Load the preferences of a sequence stored in a file.

    Parameters
    ----------
        path : unicode
            Location of the template file.

    Returns
    -------
        prefs : ConfigObj
            The data needed to rebuild the tasks.

        doc : str
            The doc of the template.

    """
    config = ConfigObj(path)
    doc = ''
    if config.initial_comment:
        doc_list = [com[1:].strip() for com in config.initial_comment]
        doc = '\n'.join(doc_list)

    return config, doc


def save_sequence_prefs(path, prefs, doc=''):
    """ Save a sequence to a file

    Parameters
    ----------
        path : unicode
            Path of the file to which save the template
        prefs : dict(str : str)
            Dictionnary containing the tempate parameters
        doc : str
            The template doc

    """
    # Create an empty ConfigObj and set filename after so that the data are
    # not loaded. Otherwise merge might lead to corrupted data.
    config = ConfigObj(indent_type='    ')
    config.filename = path
    config.merge(prefs)
    if doc:
        config.initial_comment = wrap(doc, 79)

    config.write()
